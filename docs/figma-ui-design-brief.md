# 🛍️ ECOM — Figma UI Design Brief

## What This Application Is

**ECOM** is a full-featured, production-grade e-commerce platform built on a Python microservices architecture. It supports two core user types — **Shoppers** (customers) and **Admins** (store managers). The platform handles product discovery, cart management, order placement, payment processing, real-time order tracking, and admin-side inventory & product management — all backed by event-driven, distributed backend services (FastAPI, RabbitMQ, Temporal, PostgreSQL).

---

## Pages / Screens to Design

| Screen | Description |
|---|---|
| **Landing / Hero** | Full-screen cinematic hero with brand tagline, featured collections, trending products |
| **Product Catalog** | Grid/list toggle, filters (category, price, rating), search, sort |
| **Product Detail** | Image gallery, variants, add-to-cart, reviews, related products |
| **Cart Drawer / Sidebar** | Slide-in cart panel, quantity controls, order summary |
| **Checkout** | Multi-step (address → payment → review), progress indicator |
| **Order Confirmation** | Animated success state, order ID, estimated delivery |
| **Order Tracking** | Visual timeline (placed → confirmed → shipped → delivered) |
| **User Profile / Dashboard** | Order history, saved addresses, account settings |
| **Admin Dashboard** | Product CRUD table, bulk delete, inventory counts, recent orders |
| **Admin – Add/Edit Product** | Form with image upload, category, price, stock fields |
| **Login / Sign Up** | Minimal, elegant auth screens with social login options |
| **404 / Empty States** | Creative illustrations for empty cart, no results, errors |

---

## Design Style & Aesthetic Direction

### 🎨 Visual Language
- **Theme:** Dark-first design with a rich, deep background (e.g. `#0A0A0F` near-black) contrasted by vibrant accent colors
- **Primary Accent:** Electric violet / deep indigo gradient (`#7C3AED` → `#4F46E5`)
- **Secondary Accent:** Warm amber / gold for CTAs and highlights (`#F59E0B`)
- **Surface Cards:** Glassmorphism — frosted glass effect with `backdrop-filter: blur`, subtle `1px` border with 10–15% white opacity
- **Typography:**
  - Headlines: **Clash Display** or **Syne** (bold, editorial feel)
  - Body: **Inter** or **DM Sans** (clean, readable)
- **Imagery:** High-quality lifestyle product photography with cinematic depth-of-field blur

### ✨ Motion & Interaction
- Smooth page transitions (slide + fade)
- Micro-animations on button hover (scale + glow pulse)
- Cart badge count bounce animation on add
- Staggered product card entry animations (cascading fade-up)
- Skeleton loading screens instead of plain spinners
- Parallax scroll on hero section

### 🧩 Component Style
- Buttons: Pill-shaped (fully rounded), gradient fill with subtle inner glow on hover
- Cards: Floating shadow with hover lift effect (`translateY(-6px)` + box-shadow bloom)
- Inputs: Borderless with bottom-line focus animation, floating label style
- Modals: Blur overlay background, slide-up entrance animation
- Badges: Soft glow chip style (e.g. "In Stock", "New Arrival", "Hot 🔥")

### 📐 Layout Principles
- **Grid:** 12-column, 80px max-width container (`1440px`)
- **Spacing:** 8px base grid system
- **Border Radius:** `16px` for cards, `999px` for pills, `12px` for inputs
- **Elevation:** 4-layer shadow system (none → low → mid → high)

---

## Key UX Requirements

1. **Mobile-first responsive** — design for 375px, 768px, 1280px, 1440px breakpoints
2. **Admin vs Customer split** — admin panel should feel like a premium SaaS dashboard (dark sidebar, data tables, stat cards)
3. **Cart is always accessible** — persistent floating cart icon / drawer, never a full-page redirect
4. **Order flow is linear & guided** — clear step indicators, no dead ends
5. **Empty states are delightful** — custom illustrated states for no products, empty cart, no orders

---

## Inspiration References

Look and feel inspiration from:
- **Awwwards.com** top e-commerce winners
- **Stripe's** dashboard aesthetic for admin panel
- **Apple.com** product detail page for whitespace mastery
- **Mytheresa / SSENSE** for luxury dark-mode e-commerce
- **Framer.com** for glass cards and motion principles

---

## Deliverables Expected from Figma Designer

- [ ] Full component library (design system tokens — colors, type scale, spacing, shadows, icons)
- [ ] All 12 screens in desktop (1440px) + mobile (375px)
- [ ] Interactive prototype with key flows: Browse → PDP → Cart → Checkout → Confirmation
- [ ] Admin flow: Login → Dashboard → Add Product → View Orders
- [ ] Dark mode only (light mode optional stretch goal)
- [ ] Handoff-ready with all layers named, auto-layout applied, and variables set

---

> **Goal:** Design the most visually stunning, conversion-optimised e-commerce UI in the market — one that feels like a luxury brand experience, not a generic template. Every screen should look like it could win an Awwwards site of the day.
