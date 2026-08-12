# auth-frontend

React + TypeScript frontend for the Auth Starter project. Provides email-based authentication flows (register, login, forgot password, reset password) and a protected profile page.

---

## Tech stack

| Tool | Version | Purpose |
|---|---|---|
| React | 18 | UI framework |
| TypeScript | 5 | Static typing |
| Vite | 5 | Dev server and bundler |
| React Router | 6 | Client-side routing |
| Vitest | 2 | Unit testing |
| Testing Library | 16 | Component and DOM testing |

---

## Project structure

```
auth-frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env.example
└── src/
    ├── main.tsx               # React entry point
    ├── App.tsx                # Router and route guards
    ├── api/
    │   └── auth.ts            # API client (login, register, me, logout, refresh, forgotPassword, resetPassword)
    ├── context/
    │   └── AuthContext.tsx    # AuthContext + AuthProvider
    ├── hooks/
    │   └── useAuthForm.ts     # Controlled-input form hook with client-side validation
    ├── components/
    │   ├── RequireAuth.tsx    # Redirects unauthenticated users to /login
    │   └── RequireGuest.tsx   # Redirects authenticated users to /profile
    ├── features/
    │   └── auth/
    │       └── pages/
    │           ├── LoginPage.tsx
    │           ├── RegisterPage.tsx
    │           ├── ForgotPasswordPage.tsx
    │           └── ResetPasswordPage.tsx
    ├── pages/
    │   └── ProfilePage.tsx
    └── styles/
        └── tokens.css         # CSS custom properties from design tokens
```

---

## Environment variables

All variables consumed by the frontend must be prefixed with `VITE_` so Vite
injects them at build time. Copy `.env.example` to `.env` and fill in the values
before running the dev server.

| Variable | Required | Default (example) | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` | Base URL of the auth backend. Used by the Vite dev-server proxy and the API client. In production, set this to the public backend origin. |

### `.env.example`

```dotenv
# API base URL used by the Vite dev server proxy and the frontend API client
VITE_API_BASE_URL=http://localhost:8000
```

> **Note:** Never commit a `.env` file containing real secrets. `.env` is listed
> in `.gitignore`.

---

## Local development setup

### Prerequisites

- Node.js ≥ 20
- npm ≥ 10 (bundled with Node.js 20)
- The auth backend running on `http://localhost:8000` (see `auth-backend/README.md`)

### Steps

1. **Install dependencies**

   ```bash
   cd auth-frontend
   npm install
   ```

2. **Create your local env file**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` if your backend runs on a different port or host.

3. **Start the dev server**

   ```bash
   npm run dev
   ```

   Vite starts on `http://localhost:5173` by default. All requests to `/api/v1`
   are proxied to `VITE_API_BASE_URL` (see `vite.config.ts`), so there are no
   CORS issues during development.

4. **Open the app**

   Navigate to `http://localhost:5173` in your browser.

---

## Available scripts

| Script | Command | Description |
|---|---|---|
| `dev` | `npm run dev` | Start Vite dev server with HMR |
| `build` | `npm run build` | Type-check then build for production (`dist/`) |
| `test` | `npm test` | Run unit tests once with Vitest |
| `test:watch` | `npm run test:watch` | Run Vitest in watch mode |
| `lint` | `npm run lint` | ESLint across `src/` (zero warnings allowed) |

---

## Production build

```bash
npm run build
```

The compiled output is written to `dist/`. Serve it with any static file host
(Nginx, Caddy, Vercel, etc.). Set the `VITE_API_BASE_URL` environment variable
to the production backend URL at build time:

```bash
VITE_API_BASE_URL=https://api.example.com npm run build
```

Configure your static host to redirect all unmatched paths to `index.html` so
client-side routing works correctly.

---

## Authentication flows

| Route | Guard | Page |
|---|---|---|
| `/login` | `RequireGuest` | `LoginPage` |
| `/register` | `RequireGuest` | `RegisterPage` |
| `/forgot-password` | `RequireGuest` | `ForgotPasswordPage` |
| `/reset-password` | `RequireGuest` | `ResetPasswordPage` |
| `/profile` | `RequireAuth` | `ProfilePage` |

- **`RequireAuth`** — redirects unauthenticated users to `/login`.
- **`RequireGuest`** — redirects already-authenticated users to `/profile`.
- Auth state is managed by `AuthContext` (see `src/context/AuthContext.tsx`).

---

## API client

`src/api/auth.ts` exports the following functions that map 1-to-1 to backend
endpoints:

| Function | Method | Path |
|---|---|---|
| `login` | POST | `/api/v1/auth/login` |
| `register` | POST | `/api/v1/auth/register` |
| `forgotPassword` | POST | `/api/v1/auth/forgot-password` |
| `resetPassword` | POST | `/api/v1/auth/reset-password` |
| `me` | GET | `/api/v1/auth/me` |
| `logout` | POST | `/api/v1/auth/logout` |
| `refresh` | POST | `/api/v1/auth/refresh` |

---

## Styling

Design tokens are declared as CSS custom properties in `src/styles/tokens.css`
and imported globally. Components use BEM-like class names (`.auth-card`,
`.auth-card__field`, `.field--error`). No hard-coded colors, spacing, radii, or
font sizes are allowed in component files.

---

## Testing

Unit tests use Vitest and Testing Library. Focus areas:

- **Validation module** — asserts exact error messages for every rule in
  `validation-rules.json`.
- **Route guards** — `RequireAuth` and `RequireGuest` redirect correctly.

Run tests:

```bash
npm test
```

---

## Linting and formatting

- **ESLint** (`eslint-plugin-react`, `eslint-plugin-react-hooks`,
  `eslint-plugin-react-refresh`, `@typescript-eslint`) — zero warnings policy.
- **Prettier** defaults: 2-space indent, single quotes, semicolons.

```bash
npm run lint
```

---

## Related

- Backend: [`auth-backend/README.md`](../auth-backend/README.md)
- Project root: [`README.md`](../README.md)
- Docker Compose (full stack): [`docker-compose.yml`](../docker-compose.yml)
