import http from 'k6/http';
import {check, fail, sleep} from 'k6';
import {Rate} from 'k6/metrics';

const base = __ENV.SGWA_LOAD_TEST_URL || 'http://frontend';
if (!['http://frontend', 'http://127.0.0.1:18080'].includes(base)) {
  throw new Error('Gunakan alamat project uji SGWA.');
}
const rateLimited = new Rate('rate_limited');
const scenarios = [
  ['Penggantian KTP', 'KTP saya hilang dan saya ingin meminta informasi cara mengurus penggantian.'],
  ['Jalan kabupaten rusak', 'Aspal di jalan kabupaten dekat pasar berlubang dan perlu diperbaiki.'],
  ['Lampu merah padam', 'Lampu lalu lintas di simpang dekat terminal padam sejak kemarin.'],
];

export const options = {
  scenarios: {
    citizen_workflow: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        {duration: '15s', target: 3},
        {duration: '45s', target: 5},
        {duration: '15s', target: 0},
      ],
      gracefulRampDown: '10s',
    },
  },
  summaryTrendStats: ['avg', 'med', 'p(95)', 'p(99)', 'max'],
  thresholds: {
    checks: ['rate>0.99'],
    'http_req_failed{phase:workflow}': ['rate<0.01'],
    'http_req_duration{phase:workflow}': ['p(95)<1000'],
    rate_limited: ['rate<0.01'],
  },
  noCookiesReset: true,
};

export function setup() {
  const marker = http.get(base + '/sgwa-load-test.txt', {redirects: 0});
  if (marker.status !== 200 || marker.body.trim() !== 'sgwa-disposable-load-test') {
    fail('Target harus memakai overlay load-test SGWA.');
  }
  const csrf = http.get(base + '/api/v1/auth/csrf');
  if (csrf.status !== 200) fail('Bootstrap CSRF gagal.');
  const csrfToken = csrf.json('csrf_token');
  const login = http.post(base + '/api/v1/auth/login', JSON.stringify({
    email: 'warga@demo.sgwa.id', password: __ENV.DEMO_PASSWORD,
  }), {
    headers: {'Origin': base, 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken},
    cookies: {sgwa_csrf: csrfToken},
    redirects: 0,
  });
  if (login.status !== 200 || !login.cookies.sgwa_session?.length) fail('Login akun uji gagal.');
  return {session: login.cookies.sgwa_session[0].value, csrf: login.json('csrf_token')};
}

export default function (auth) {
  const params = {
    headers: {'Origin': base, 'Content-Type': 'application/json', 'X-CSRF-Token': auth.csrf},
    cookies: {sgwa_session: auth.session, sgwa_csrf: auth.csrf},
    tags: {phase: 'workflow'},
    redirects: 0,
  };
  const [title, description] = scenarios[(__VU + __ITER) % scenarios.length];
  const submitted = http.post(base + '/api/v1/requests', JSON.stringify({
    title: '[Uji beban] ' + title,
    description,
  }), {...params, tags: {...params.tags, name: 'POST /requests'}});
  rateLimited.add(submitted.status === 429);
  if (check(submitted, {'permohonan dibuat': response => response.status === 201})) {
    const id = submitted.json('id');
    const details = http.get(base + '/api/v1/requests/' + id, {
      ...params, tags: {...params.tags, name: 'GET /requests/:id'},
    });
    check(details, {'detail dapat dibaca pemohon': response => response.status === 200 && response.json('id') === id});
  }
  const list = http.get(base + '/api/v1/requests', {...params, tags: {...params.tags, name: 'GET /requests'}});
  check(list, {'daftar permohonan tersedia': response => response.status === 200 && Array.isArray(response.json('items'))});
  sleep(2);
}
