# AI Learning Coach - Pages Overview

## Page Structure and Features

### 1. Dashboard (`/`)
**Purpose**: Main landing page with overview of user's learning journey

**Sections**:
- **Hero Section**
  - Large gradient heading: "Welcome to Your AI Learning Coach"
  - Subtitle explaining the platform

- **Stats Cards** (3 cards in a row)
  - **Active Goal Card** (Blue gradient)
    - Shows if user has an active goal
    - Displays goal text preview
    - Shows goal count

  - **Total Sources Card** (Purple gradient)
    - Shows active sources count
    - Displays total sources

  - **Latest Digest Card** (Pink/Red gradient)
    - Shows number of items in latest digest
    - Displays generation date

- **Quick Actions** (3 action cards)
  - **Create Goal** - Links to /goals (Blue gradient)
  - **Add Source** - Links to /sources (Purple gradient)
  - **View Digests** - Links to /digests (Pink/Red gradient)

---

### 2. Goals Page (`/goals`)
**Purpose**: Create and manage learning goals

**Sections**:
- **Current Active Goal Display**
  - Shows goal text in a prominent card
  - Displays difficulty level badge
  - Displays frequency badge
  - Shows creation date
  - "Active" status indicator

- **Create/Update Goal Form**
  - **Goal Text**: Large textarea for describing learning objective
  - **Difficulty Level**: Dropdown
    - Beginner - "I'm just starting out"
    - Intermediate - "I have some knowledge"
    - Advanced - "I'm experienced"
  - **Frequency**: Dropdown
    - Daily - "Receive content every day"
    - Weekly - "Receive content once a week"
    - Biweekly - "Receive content every two weeks"
  - Submit button with loading state

**User Flow**:
1. View current active goal (if exists)
2. Fill out form to create new goal or update existing
3. Submit and see immediate feedback
4. Goal card updates with new information

---

### 3. Sources Page (`/sources`)
**Purpose**: Manage content sources for learning material

**Sections**:
- **Seed Default Sources** (shown when no sources exist)
  - Large call-to-action card
  - Button to add 4 default RSS feeds:
    - Hacker News RSS
    - Reddit Programming
    - Reddit Machine Learning
    - Google AI Blog

- **Add Custom Source Form**
  - **Source Type**: Dropdown
    - RSS Feed
    - YouTube Channel
    - Reddit
    - X/Twitter
    - Website
  - **Source URL**: Text input for URL or identifier
  - Submit button with loading state

- **Sources List** (Grid layout)
  - Each source card shows:
    - Source type icon (RSS, YouTube, Reddit, etc.)
    - Status badge (Active/Disabled/Error)
    - Source URL in monospace font
    - Creation date
    - Last fetched date (if available)
  - Hover effects for interactivity
  - "Add Defaults" button in header (when sources exist)

**User Flow**:
1. Start with empty state → Click "Add Default Sources"
2. OR add custom source via form
3. View all sources in grid
4. See status and fetch information for each

---

### 4. Digests Page (`/digests`)
**Purpose**: View and interact with generated learning digests

**Sections**:

#### List View (Initial)
- **Digest History Cards**
  - Goal text preview (first 60 chars)
  - Date range (week_start_date to week_end_date)
  - Total items count badge
  - Generation date
  - Click to expand to detail view

#### Detail View (After clicking a digest)
- **Back Button** - Return to list view

- **Digest Header**
  - Full goal text
  - Date range with calendar icon
  - Generation date with clock icon
  - Total items count in prominent badge

- **Digest Items** (List of content)
  Each item card includes:
  - **Item Number** - Circular badge (1, 2, 3...)
  - **Title** - Main heading
  - **Badges**:
    - Source type (RSS, YouTube, etc.)
    - Relevance score
  - **Summary Section** - Gray box with content summary
  - **Why It Matters Section** - Blue box explaining relevance
  - **Read More Link** - External link to original content
  - **Feedback Buttons**:
    - Thumbs up (Useful)
    - Thumbs down (Not Useful)
    - Shows "Feedback Submitted" after click

**User Flow**:
1. View list of all digests
2. Click on digest to expand
3. Read through items
4. Click external links to read full content
5. Provide feedback on each item
6. Navigate back to list

---

## Design System

### Color Gradients
- **Blue-Indigo-Purple**: Goals, primary actions
- **Purple-Pink-Red**: Sources, secondary actions
- **Pink-Red-Orange**: Digests, tertiary actions

### Component Patterns
- **Card with Blur Effect**: White card with gradient blur shadow
- **Icon Badges**: Circular or rounded rectangles with gradient backgrounds
- **Status Indicators**: Colored pills showing Active/Disabled/Error
- **Loading States**: Spinning gradients
- **Hover Effects**: Scale + shadow increase

### Typography
- **Hero Headings**: 5xl-6xl with gradients
- **Section Headings**: 2xl-3xl bold
- **Body Text**: Base to lg, gray-700
- **Labels**: Small, semibold, gray-700

### Spacing
- Section margin: 12 (mb-12)
- Card padding: 8 (p-8)
- Element spacing: 4-6 (space-x-4, gap-6)

---

## Navigation Flow

```
Dashboard (/)
├── Click "Create Goal" → Goals Page (/goals)
├── Click "Add Source" → Sources Page (/sources)
└── Click "View Digests" → Digests Page (/digests)

Goals Page (/goals)
└── Create goal → Stay on page with updated view

Sources Page (/sources)
└── Add sources → Stay on page with updated grid

Digests Page (/digests)
├── Click digest → Detail view (same page)
└── Click back → List view (same page)
```

---

## Mobile Responsiveness

- **Dashboard**: Stack stats cards vertically on mobile
- **Goals**: Form elements stack, full width on mobile
- **Sources**: Grid becomes single column on mobile
- **Digests**: Cards stack, simplified layout on mobile
- **Navigation**: Condensed on mobile, possibly hamburger menu

---

## Loading & Error States

### Loading
- Skeleton screens with pulsing animations
- Spinner icons where appropriate
- Disabled buttons during submission

### Empty States
- Friendly illustrations or icons
- Clear call-to-action messages
- Helpful guidance text

### Error States
- Alert messages at top of forms
- Inline validation errors
- Retry buttons where applicable

---

## Accessibility Features

- Semantic HTML (nav, main, article, section)
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus states on all interactive elements
- Alt text on icons (via SVG titles)
- Color contrast ratios meet WCAG AA standards

---

This overview provides a complete picture of the frontend structure and user experience!
