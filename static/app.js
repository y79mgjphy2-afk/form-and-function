const $ = id => document.getElementById(id);
let csrf = '';
let currentPlan = null;
let currentMode = 'demo';
const completedWorkouts = new Set();

function addTextElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text;
  return element;
}

function renderPlan(plan, mode) {
  currentPlan = plan;
  currentMode = mode;
  completedWorkouts.clear();
  $('summary').textContent = plan.summary;
  $('plan-mode').textContent = mode === 'live' ? 'PERSONALIZED AI PLAN' : 'DEMO PLAN';
  const workouts = $('workouts');
  workouts.replaceChildren();
  plan.workouts.forEach((workout, index) => {
    const card = document.createElement('article');
    card.className = 'card workout';
    card.append(addTextElement('div', 'workout-day', workout.day));
    card.append(addTextElement('h3', '', workout.focus));
    const list = document.createElement('div');
    list.className = 'exercise-list';
    for (const exercise of workout.exercises) {
      const row = document.createElement('div');
      row.className = 'exercise';
      row.append(addTextElement('b', '', exercise.name));
      row.append(addTextElement('span', '', `${exercise.sets} sets · ${exercise.reps}`));
      row.append(addTextElement('small', '', `Rest ${exercise.rest}`));
      list.append(row);
    }
    card.append(list);
    const complete = document.createElement('button');
    complete.type = 'button';
    complete.className = 'complete-workout';
    complete.dataset.index = String(index);
    complete.setAttribute('aria-pressed', 'false');
    complete.textContent = 'Mark workout complete';
    complete.addEventListener('click', () => {
      if (completedWorkouts.has(index)) completedWorkouts.delete(index);
      else completedWorkouts.add(index);
      complete.setAttribute('aria-pressed', String(completedWorkouts.has(index)));
      complete.textContent = completedWorkouts.has(index) ? '✓ Workout complete' : 'Mark workout complete';
      complete.classList.toggle('is-complete', completedWorkouts.has(index));
      updateProgress();
    });
    card.append(complete);
    workouts.append(card);
  });
  const tips = $('tips');
  tips.replaceChildren(...plan.tips.map(tip => addTextElement('li', '', tip)));
  updateProgress();
  $('results').classList.remove('hidden');
}

function updateProgress() {
  if (!currentPlan) return;
  const total = currentPlan.workouts.length;
  const count = completedWorkouts.size;
  const percent = total ? Math.round(count / total * 100) : 0;
  $('progress-count').textContent = `${count} of ${total} workouts complete`;
  $('progress-fill').style.width = `${percent}%`;
  document.querySelector('[role="progressbar"]').setAttribute('aria-valuenow', String(percent));
}

async function postPlan(data) {
  const response = await fetch('/api/plan', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
    body: JSON.stringify(data),
  });
  let result;
  try {
    result = await response.json();
  } catch {
    throw new Error('The server returned an unexpected response. Refresh the page and try again.');
  }
  if (!response.ok) throw new Error(result.error || 'Could not create a plan.');
  return result;
}

function downloadPlan() {
  if (!currentPlan) return;
  const exportData = {
    app: 'Form & Function',
    createdAt: new Date().toISOString(),
    mode: currentMode,
    preferences: {
      goal: $('goal').value,
      experience: $('experience').value,
      daysPerWeek: Number($('days').value),
      equipment: $('equipment').value,
    },
    plan: currentPlan,
    completedWorkouts: [...completedWorkouts].map(index => currentPlan.workouts[index].day),
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(exportData, null, 2)], {type: 'application/json'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'form-and-function-workout-plan.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$('download-plan').addEventListener('click', downloadPlan);
$('print-plan').addEventListener('click', () => window.print());

$('plan-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = $('generate');
  button.disabled = true;
  button.firstChild.textContent = 'Building your plan… ';
  $('message').textContent = '';
  try {
    const result = await postPlan({
      goal: $('goal').value,
      experience: $('experience').value,
      days: Number($('days').value),
      equipment: $('equipment').value,
      limitations: $('limitations').value,
      mode: $('mode').value,
    });
    renderPlan(result.plan, result.mode);
    $('results').scrollIntoView({behavior: 'smooth', block: 'start'});
  } catch (error) {
    $('message').textContent = error.message;
  } finally {
    button.disabled = false;
    button.firstChild.textContent = 'Build my plan ';
  }
});

fetch('/api/config')
  .then(response => {
    if (!response.ok) throw new Error('Coach configuration unavailable.');
    return response.json();
  })
  .then(config => {
    csrf = config.csrf;
    $('mode').options[1].disabled = !config.live;
    if (config.live) $('mode').options[1].textContent = 'Live AI · server configured';
    $('generate').disabled = false;
  })
  .catch(error => {
    $('message').textContent = error.message;
    $('generate').disabled = true;
  });
