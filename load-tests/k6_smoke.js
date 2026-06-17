import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const restaurants = http.get(`${BASE_URL}/api/v1/restaurants?city=Bengaluru&limit=20`);
  check(restaurants, {
    'restaurants status is 200': (r) => r.status === 200,
  });

  const ready = http.get(`${BASE_URL}/api/v1/health/ready`);
  check(ready, {
    'ready status is 200': (r) => r.status === 200,
  });

  sleep(1);
}
