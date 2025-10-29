# Frontend Template

**⚠️ This is a TEMPLATE directory - not a working frontend!**

## Purpose

This directory contains the **template** for the auto-generated frontend.

When you run `make codegen`, this template is:
1. **Copied** to `.run_cache/generated_frontend/`
2. **Processed** to replace placeholders with actual model data
3. **Populated** with generated pages for each model

## What's Here

- `package.json` - Static dependencies
- `tsconfig.json` - TypeScript config
- `vite.config.ts` - Vite build config
- `index.html` - HTML entry point
- `src/main.tsx` - React entry point (static)
- `src/App.tsx.template` - App component with placeholders
- `src/pages/` - Empty (pages are generated)
- `src/config/` - Empty (config is generated)

## Placeholders in App.tsx.template

- `{%IMPORTS%}` - Replaced with model page imports
- `{%ROUTES%}` - Replaced with React Router routes

## How Generation Works

```
core/frontend_template/       ← This directory (template)
         ↓
    [Copy entire directory]
         ↓
.run_cache/generated_frontend/ ← Working frontend
         ↓
    [Replace placeholders]
         ↓
    [Generate pages]
         ↓
    [npm install]
         ↓
    [npm run dev]
```

## Customizing

To customize the frontend:

1. **Edit template files here** (in `core/frontend_template/`)
2. **Run** `make codegen` to regenerate
3. **Do NOT** edit files in `.run_cache/generated_frontend/` (they'll be overwritten)

## Examples

### Adding a custom style

Edit `src/App.tsx.template`:
```typescript
import "./custom.css";  // Add this
```

Then add `src/custom.css` to this template directory.

### Changing the theme

Edit `src/App.tsx.template`:
```typescript
<ConfigProvider theme={RefineThemes.Purple}>  // Change from Blue
```

### Adding custom routes

Edit `src/App.tsx.template` and add routes above `{%ROUTES%}`:
```typescript
<Route path="/dashboard" element={<Dashboard />} />
{%ROUTES%}
```

---

**Remember:** This is a template. The actual working frontend is in `.run_cache/generated_frontend/`.
