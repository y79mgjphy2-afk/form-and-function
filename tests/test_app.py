import json
import unittest
from unittest.mock import MagicMock, patch

import app as module


class FitnessCoachTests(unittest.TestCase):
    def setUp(self):
        module.app.config['TESTING'] = True
        self.client = module.app.test_client()
        self.csrf = self.client.get('/api/config').json['csrf']

    def post(self, data):
        return self.client.post('/api/plan', json=data, headers={'X-CSRF-Token': self.csrf})

    def profile(self, **overrides):
        values = {
            'goal': 'strength',
            'experience': 'beginner',
            'days': 3,
            'equipment': 'dumbbells',
            'limitations': '',
            'mode': 'demo',
        }
        values.update(overrides)
        return values

    def test_demo_plan_matches_requested_days_and_equipment(self):
        response = self.post(self.profile(days=4, equipment='bands'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['mode'], 'demo')
        plan = response.json['plan']
        self.assertEqual(len(plan['workouts']), 4)
        self.assertEqual(plan['workouts'][1]['exercises'][1]['name'], 'Band row')
        self.assertTrue(plan['tips'])

    def test_invalid_profiles_are_rejected(self):
        self.assertEqual(self.post(self.profile(days=0)).status_code, 400)
        self.assertEqual(self.post(self.profile(goal='medical_diagnosis')).status_code, 400)
        self.assertEqual(self.post(self.profile(goal=[])).status_code, 400)
        self.assertEqual(self.post(self.profile(experience={})).status_code, 400)
        self.assertEqual(self.post(self.profile(days=True)).status_code, 400)
        self.assertEqual(self.post(self.profile(limitations='x' * 501)).status_code, 400)

    def test_csrf_required_and_live_requires_key(self):
        self.assertEqual(self.client.post('/api/plan', json=self.profile()).status_code, 403)
        with patch.dict(module.os.environ, {'OPENAI_API_KEY': ''}):
            self.assertEqual(self.post(self.profile(mode='live')).status_code, 400)

    def test_live_plan_uses_provider_and_validates_response(self):
        plan = module.demo_plan('strength', 'beginner', 2, 'bodyweight')
        body = {'output': [{'content': [{'type': 'output_text', 'text': json.dumps(plan)}]}]}
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(body).encode()
        with patch.dict(module.os.environ, {'OPENAI_API_KEY': 'fake-test-key'}), patch(
            'app.urllib.request.urlopen', return_value=response
        ):
            result = self.post(self.profile(days=2, mode='live'))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json['mode'], 'live')
        self.assertEqual(len(result.json['plan']['workouts']), 2)

    def test_live_plan_rejects_malformed_provider_output(self):
        body = {'output': [{'content': [{'type': 'output_text', 'text': '{}'}]}]}
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(body).encode()
        with patch.dict(module.os.environ, {'OPENAI_API_KEY': 'fake-test-key'}), patch(
            'app.urllib.request.urlopen', return_value=response
        ):
            result = self.post(self.profile(mode='live'))
        self.assertEqual(result.status_code, 502)
        self.assertIn('failed', result.json['error'])

    def test_static_assets_and_security_headers(self):
        for url in ('/', '/static/app.js', '/static/style.css'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])
            response.close()


if __name__ == '__main__':
    unittest.main()
