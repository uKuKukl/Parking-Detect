# Frontend Redesign Design

## Goal

Redesign the Vue 3 + Element Plus frontend into a clean, modern, light administrative interface suitable for a graduation/demo presentation. The redesign should make the system feel like a complete parking violation management platform while keeping the current features and routes intact.

## Approved Visual Direction

Use a clean light-government/admin style:

- Page background: soft gray-blue (`#f5f7fb` range).
- Primary color: professional blue (`#2563eb` range).
- Layout: white card-like sidebar, white top header, rounded content panels.
- Tone: minimal, tidy, trustworthy, and easy to read.
- Avoid a heavy dark “old admin template” look.
- Use subtle shadows, soft borders, clear spacing, and consistent radii.

## Scope

Redesign these frontend areas:

1. Global app shell in `App.vue`.
2. Login page.
3. Dashboard page, including stats, trends, heatmaps, rankings, and latest records.
4. Audit/review page, including filters, upload controls, table, pagination, dialogs, and image preview.
5. Report page, including filters, report cards, and export actions.
6. Camera management page.
7. ROI settings page.
8. Audit log page.
9. System settings page.

No backend behavior changes are required for this redesign.

## Architecture

Create a lightweight design system in the existing frontend without over-abstracting the app.

### Global CSS

Add a global stylesheet, for example `frontend/src/styles/admin.css`, and import it from `frontend/src/main.js` or `App.vue`.

It should define:

- CSS variables for colors, radius, shadow, spacing, and typography.
- Base body background and font smoothing.
- Common utility classes:
  - `.page-shell`
  - `.page-header`
  - `.page-title`
  - `.page-subtitle`
  - `.toolbar-card`
  - `.content-card`
  - `.stat-grid`
  - `.stat-card`
  - `.section-grid`
- Element Plus overrides for cards, tables, buttons, inputs, pagination, dialogs, menus, and tags.

### Global Layout

Update `App.vue` to use:

- A white rounded sidebar with logo block and menu items.
- A soft gray-blue application background.
- A white top header with title, subtitle, user role tag, and logout button.
- A scrollable main content area with consistent padding.

The route/menu structure stays unchanged.

### Page-Level Structure

Each page should follow a common structure:

```vue
<div class="page-shell">
  <div class="page-header">
    <div>
      <h2 class="page-title">Page title</h2>
      <p class="page-subtitle">Short page description</p>
    </div>
    <div class="page-actions">...</div>
  </div>

  <div class="toolbar-card">filters/actions</div>
  <div class="content-card">main content</div>
</div>
```

Pages that do not need filters can omit `.toolbar-card`.

## Component Design

### Sidebar

- Width around 236px.
- White background, rounded right-side/card style.
- Logo block with blue square icon and two-line text.
- Menu items use pill-shaped active state.
- Active item: light blue background and blue text.
- Inactive items: muted slate text.

### Header

- Height around 68px.
- White background with subtle shadow/border.
- Left: current system/page identity.
- Right: user display, role tag, logout button.
- Remove emoji from username display for a more professional look.

### Cards and Tables

- Cards use border radius around 16px and subtle shadow.
- Tables use soft header background, less visual noise, rounded wrapper, and consistent action button spacing.
- Filter rows use white cards with flex wrapping and consistent gaps.

### Dashboard

The dashboard should be the most polished page:

- Stat cards use left accent bars and large numeric values.
- Trend section uses clean progress bars or compact visual bars.
- Location heatmap uses blue heat colors instead of red-heavy colors, matching the main design.
- Hour heatmap uses compact rounded cells with hover tooltips.
- Latest records table uses the shared table styling.

### Login Page

Redesign as a centered login card on a soft gradient/light background:

- Left or top branding for the system.
- Clean card with username/password fields.
- Blue primary login button.
- Keep current authentication behavior unchanged.

## Data Flow

No data contracts change.

Existing API calls remain unchanged. The redesign only changes presentation and CSS classes.

## Error Handling

Keep existing request interceptor and Element Plus messages. Do not introduce new error handling behavior unless needed for UI consistency.

## Accessibility and Responsiveness

- Maintain readable contrast for text, links, active menus, and buttons.
- Use visible hover/focus states from Element Plus or CSS overrides.
- Ensure toolbar controls wrap on narrower screens.
- The layout should remain usable on common laptop widths.
- Avoid tiny text below 12px for functional UI.

## Implementation Notes

- Prefer shared CSS classes over duplicating inline styles.
- Remove or reduce inline styles in the touched pages where practical.
- Do not create many new Vue components unless the page becomes hard to maintain.
- Keep the redesign focused on frontend appearance; do not change backend APIs.
- Do not add new dependencies or chart libraries for this pass.

## Validation

Run:

```bash
npm run build --prefix frontend
```

Optionally run backend tests if backend files are touched, but this redesign should not require backend changes.

## Out of Scope

- Replacing Element Plus.
- Adding a charting library.
- Changing authentication or authorization behavior.
- Changing backend APIs.
- Mobile-first redesign for phone-sized screens.
