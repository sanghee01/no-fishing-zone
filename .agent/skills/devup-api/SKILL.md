---
name: devup-api
description: |
  Type-safe API client generator from OpenAPI schemas with full ecosystem support.

  TRIGGER WHEN:
  - Setting up API client with OpenAPI schema (@devup-api/fetch)
  - Making typed API requests (GET, POST, PUT, PATCH, DELETE)
  - Using React Query hooks (@devup-api/react-query)
  - Creating CRUD interfaces (@devup-api/ui)
  - Configuring Vite/Next.js/Webpack/Rsbuild plugins
  - Implementing authentication middleware
  - Using DevupObject for type references
---

# devup-api Usage Guide

Type-safe API client from OpenAPI. Zero generics, auto-generated types.

## Setup

### Install

```bash
# Core + Build Plugin (choose one)
npm install @devup-api/fetch @devup-api/vite-plugin      # Vite
npm install @devup-api/fetch @devup-api/next-plugin      # Next.js
npm install @devup-api/fetch @devup-api/webpack-plugin   # Webpack
npm install @devup-api/fetch @devup-api/rsbuild-plugin   # Rsbuild

# Optional Integrations
npm install @devup-api/react-query @tanstack/react-query  # React Query
npm install @devup-api/ui  # CRUD UI
```

### Configure Build Tool

```ts
// vite.config.ts
import devupApi from "@devup-api/vite-plugin";
export default defineConfig({ plugins: [devupApi()] });

// next.config.ts
import devupApi from "@devup-api/next-plugin";
export default devupApi({ reactStrictMode: true });
```

### tsconfig.json

```json
{ "include": ["src", "df/**/*.d.ts"] }
```

Place `openapi.json` in project root, run `npm run dev`.

---

## @devup-api/fetch — API Client

### Create Client

```ts
import { createApi, type DevupObject } from "@devup-api/fetch";

const api = createApi("https://api.example.com");
// or with options
const api = createApi({
  baseUrl: "https://api.example.com",
  headers: { "X-Custom": "value" },
});
```

### HTTP Methods

```ts
// GET
const users = await api.get("getUsers", { query: { page: 1, limit: 20 } });
const user = await api.get("/users/{id}", { params: { id: "123" } });

// POST
const created = await api.post("createUser", {
  body: { name: "John", email: "john@example.com" },
});

// PUT / PATCH / DELETE
await api.put("/users/{id}", {
  params: { id: "1" },
  body: { name: "Jane", email: "jane@example.com" },
});
await api.patch("/users/{id}", { params: { id: "1" }, body: { name: "Jane" } });
await api.delete("/users/{id}", { params: { id: "1" } });
```

### Response Handling

```ts
const result = await api.get("getUser", { params: { id: "1" } });

if (result.data) {
  console.log(result.data.name); // typed response
} else if (result.error) {
  console.error(result.error); // typed error
}
console.log(result.response.status); // raw Response
```

### DevupObject (Type References)

Use `DevupObject` directly in type annotations without redefining types:

```ts
// Direct usage in variable declarations
const user: DevupObject["User"] = await fetchUser();
const body: DevupObject<"request">["CreateUserBody"] = {
  name: "John",
  email: "john@example.com",
};
const error: DevupObject<"error">["ErrorResponse"] = result.error;

// Direct usage in function parameters
function displayUser(user: DevupObject["User"]) {
  /* ... */
}

// Direct usage in component props
function UserCard({ user }: { user: DevupObject["User"] }) {
  /* ... */
}

// Multi-server types
const product: DevupObject<"response", "openapi2.json">["Product"] = data;
```

### Middleware

```ts
// Auth
api.use({
  onRequest: async ({ request }) => {
    const token = localStorage.getItem("token");
    if (token) {
      const headers = new Headers(request.headers);
      headers.set("Authorization", `Bearer ${token}`);
      return new Request(request, { headers });
    }
  },
});

// Token Refresh
api.use({
  onResponse: async ({ request, response }) => {
    if (response.status === 401) {
      const newToken = await refreshToken();
      const headers = new Headers(request.headers);
      headers.set("Authorization", `Bearer ${newToken}`);
      return fetch(new Request(request, { headers }));
    }
  },
});
```

---

## @devup-api/react-query — React Query Hooks

```ts
import { createApi } from "@devup-api/fetch";
import { createQueryClient } from "@devup-api/react-query";

const api = createApi("https://api.example.com");
const queryClient = createQueryClient(api);
// hooks are now available like queryClient.useQuery
```

---

## @devup-api/ui — CRUD Components

Auto-generated CRUD from OpenAPI tags.
(Details on usage would be here based on the components library structure)
