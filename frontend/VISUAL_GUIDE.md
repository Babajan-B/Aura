# Visual Design Guide - AI Learning Coach Frontend

## Color System

### Gradient Definitions

#### Primary Gradient (Goals, Main Actions)
```css
background: linear-gradient(to right, #2563eb, #4f46e5, #7c3aed);
/* Blue-600 → Indigo-600 → Purple-600 */
```
Use for: Goal cards, primary buttons, active navigation

#### Secondary Gradient (Sources, Secondary Actions)
```css
background: linear-gradient(to right, #7c3aed, #db2777, #dc2626);
/* Purple-600 → Pink-600 → Red-600 */
```
Use for: Source cards, secondary buttons

#### Tertiary Gradient (Digests, Content)
```css
background: linear-gradient(to right, #db2777, #dc2626, #ea580c);
/* Pink-600 → Red-600 → Orange-600 */
```
Use for: Digest cards, content highlights

#### Background Gradient
```css
background: linear-gradient(to bottom right, #f8fafc, #dbeafe, #e0e7ff);
/* Slate-50 → Blue-50 → Indigo-100 */
```
Use for: Page backgrounds

---

## Component Anatomy

### Navigation Bar
```
┌─────────────────────────────────────────────────────────────┐
│ [AI] Learning Coach    Dashboard  Goals  Sources  Digests   │
│  ↑                      ↑                                    │
│  Logo                   Active link has gradient background  │
└─────────────────────────────────────────────────────────────┘
  Glassmorphism: backdrop-blur + semi-transparent white
```

### Stats Card
```
┌─────────────────────────────────────┐
│  ┌───┐                         ⟳    │ ← Loading spinner (if loading)
│  │ ✓ │  Active Goal                 │
│  └───┘  1 Goal                      │
│         Learn machine learning...   │ ← Preview text
└─────────────────────────────────────┘
   ↑         ↑
   Icon      Stat

Shadow: Gradient blur underneath
Hover: Shadow increases, slight scale
```

### Action Card
```
┌──────────────────────────────────┐
│  ╔═══╗                          │
│  ║ + ║                          │
│  ╚═══╝                          │
│                                  │
│  Create Goal                     │
│  Set a new learning objective    │
└──────────────────────────────────┘
  Gradient background
  White text
  Icon at top
  Hover: Scale + shadow increase
```

### Form Input
```
Label: Font-semibold, gray-700, mb-2
┌─────────────────────────────────────┐
│ Placeholder or value text           │
│                                     │
└─────────────────────────────────────┘
  Border: Gray-300
  Focus: Ring-2 with gradient color
  Rounded: xl (0.75rem)
  Padding: px-4 py-3
```

### Button (Primary)
```
┌─────────────────────────────────────┐
│  ✓  Create Goal                     │
└─────────────────────────────────────┘
  Background: Gradient
  Text: White, semibold
  Shadow: lg
  Hover: shadow-xl + scale-102
  Disabled: opacity-50, no hover
  Loading: Spinner + text
```

### Badge
```
┌────────────┐
│ Active     │  or  │ Intermediate │
└────────────┘      └──────────────┘
  Rounded: full
  Padding: px-3 py-1
  Text: xs, semibold
  Background: Gradient or solid color
```

---

## Page Layouts

### Dashboard Layout
```
┌─────────────────────────────────────────────────────┐
│                    Navigation                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Welcome to Your                        │
│           AI Learning Coach                         │
│    Personalized learning content delivered...      │
│                                                     │
│  ┌────────┐  ┌────────┐  ┌────────┐              │
│  │ Active │  │ Total  │  │ Latest │              │
│  │ Goal   │  │ Sources│  │ Digest │              │
│  └────────┘  └────────┘  └────────┘              │
│                                                     │
│  Quick Actions                                      │
│  ┌────────┐  ┌────────┐  ┌────────┐              │
│  │ Create │  │  Add   │  │  View  │              │
│  │ Goal   │  │ Source │  │ Digest │              │
│  └────────┘  └────────┘  └────────┘              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Goals Layout
```
┌─────────────────────────────────────────────────────┐
│                    Navigation                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│                 Learning Goals                      │
│       Set your learning objectives...               │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Active Goal                            🟢   │  │
│  │ Learn machine learning and AI...            │  │
│  │ [Intermediate] [Weekly]                     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Create New Goal                             │  │
│  │                                             │  │
│  │ What do you want to learn?                  │  │
│  │ ┌─────────────────────────────────────┐    │  │
│  │ │ Textarea...                         │    │  │
│  │ └─────────────────────────────────────┘    │  │
│  │                                             │  │
│  │ Difficulty Level                            │  │
│  │ [Dropdown ▼]                                │  │
│  │                                             │  │
│  │ Frequency                                   │  │
│  │ [Dropdown ▼]                                │  │
│  │                                             │  │
│  │ [Create Goal Button]                        │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Sources Layout
```
┌─────────────────────────────────────────────────────┐
│                    Navigation                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Content Sources                        │
│       Manage your learning content sources          │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Add Custom Source                           │  │
│  │ [Type ▼] [URL Input.............] [Add]     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Your Sources              [Add Defaults]     │  │
│  │                                             │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐       │  │
│  │  │ 📡 RSS │  │ 🔴 YT  │  │ 👽 RDT │       │  │
│  │  │ Active │  │ Active │  │ Active │       │  │
│  │  │ URL... │  │ URL... │  │ URL... │       │  │
│  │  └────────┘  └────────┘  └────────┘       │  │
│  │                                             │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Digests Layout (List View)
```
┌─────────────────────────────────────────────────────┐
│                    Navigation                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Learning Digests                       │
│    Your personalized learning content delivered     │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Digest History                              │  │
│  │                                             │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │ 📄 Learn machine learn...  [10 Items]│→ │  │
│  │  │    Nov 17 - Nov 24  |  Nov 24, 2024 │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  │                                             │  │
│  │  ┌──────────────────────────────────────┐  │  │
│  │  │ 📄 Previous goal...        [8 Items] │→ │  │
│  │  │    Nov 10 - Nov 17  |  Nov 17, 2024 │  │  │
│  │  └──────────────────────────────────────┘  │  │
│  │                                             │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Digests Layout (Detail View)
```
┌─────────────────────────────────────────────────────┐
│                    Navigation                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ← Back to Digests                                  │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Learn machine learning and AI          [10]  │  │
│  │ 📅 Nov 17 - Nov 24  ⏰ Nov 24, 2024        │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ ① Introduction to Neural Networks      RSS  │  │
│  │    Score: 0.95                              │  │
│  │                                             │  │
│  │ Summary                                     │  │
│  │ ┌─────────────────────────────────────┐   │  │
│  │ │ This article explains...            │   │  │
│  │ └─────────────────────────────────────┘   │  │
│  │                                             │  │
│  │ 💡 Why It Matters                           │  │
│  │ ┌─────────────────────────────────────┐   │  │
│  │ │ Understanding neural networks...    │   │  │
│  │ └─────────────────────────────────────┘   │  │
│  │                                             │  │
│  │ Read More → │ Was this helpful? 👍 👎     │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  [More items...]                                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Interactive States

### Hover States
- **Cards**: Shadow increases, slight scale (102%)
- **Buttons**: Shadow increases, scale 105%
- **Links**: Color darkens, underline appears
- **Icons**: Color changes to accent color

### Loading States
- **Spinner**: Rotating gradient circle
- **Skeleton**: Pulsing gray shapes
- **Button**: Spinner + disabled appearance

### Active States
- **Navigation**: Gradient background
- **Form**: Ring border with focus color
- **Selected**: Highlighted with gradient

### Error States
- **Form**: Red border + error message below
- **Alert**: Red background banner at top
- **Inline**: Red text with warning icon

---

## Spacing System

### Container Widths
```
max-w-7xl: Dashboard, Sources (1280px)
max-w-6xl: Digests (1152px)
max-w-4xl: Goals (896px)
```

### Padding Scale
```
Page: px-4 sm:px-6 lg:px-8 (16-32px)
Card: p-8 (32px) or p-6 (24px)
Button: px-6 py-4 (24px, 16px)
Badge: px-3 py-1 (12px, 4px)
```

### Margin Scale
```
Section: mb-12 (48px) or mb-8 (32px)
Element: mb-6 (24px) or mb-4 (16px)
Text: mb-2 (8px) or mb-1 (4px)
```

### Gap Scale
```
Grid: gap-6 (24px) or gap-4 (16px)
Flex: space-x-4 (16px) or space-x-3 (12px)
```

---

## Responsive Breakpoints

### Mobile (< 640px)
- Single column layout
- Stack cards vertically
- Full-width buttons
- Condensed navigation
- Smaller text sizes

### Tablet (640px - 1024px)
- 2-column grid for cards
- Side-by-side action buttons
- Medium text sizes
- Full navigation

### Desktop (> 1024px)
- 3-column grid for cards
- Maximum container widths
- Full features visible
- Large text sizes

---

## Animation Timings

```css
/* Fast interactions */
duration-200: 200ms (hover, focus)

/* Standard transitions */
duration-300: 300ms (cards, buttons)

/* Slow animations */
duration-500: 500ms (fade-in, page transitions)
```

---

## Icon Usage

### Sources
- RSS: Radio waves icon
- YouTube: Play button
- Reddit: Alien head
- Twitter/X: Bird
- Website: Globe

### Actions
- Create: Plus sign
- View: Eye
- Edit: Pencil
- Delete: Trash
- Link: External link arrow

### Status
- Active: Check circle
- Loading: Spinner
- Error: Alert triangle
- Success: Check mark

### UI
- Back: Left arrow
- Forward: Right arrow
- Expand: Down chevron
- Collapse: Up chevron

---

## Typography Scale

```
Hero:    text-6xl (60px) - gradient headings
H1:      text-5xl (48px) - page titles
H2:      text-3xl (30px) - section titles
H3:      text-2xl (24px) - card titles
H4:      text-xl (20px) - subsections
Body:    text-base (16px) - main content
Small:   text-sm (14px) - labels
Tiny:    text-xs (12px) - badges, meta
```

---

## Shadow System

```css
/* Cards default */
shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1)

/* Cards hover */
shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1)

/* Buttons and badges */
shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1)

/* Navigation */
shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
```

---

## Best Practices

1. **Consistency**: Use the same gradients for similar elements
2. **Hierarchy**: Larger elements have more visual weight
3. **Spacing**: Maintain consistent spacing throughout
4. **Feedback**: Always show loading/success/error states
5. **Accessibility**: High contrast, clear focus states
6. **Performance**: Optimize animations, use transforms

---

This visual guide ensures consistent, beautiful design across the entire application!
