# AI Learning Coach - Modern Frontend

A beautiful, modern Next.js frontend for the AI Learning Coach application.

## Features Built

### 1. **Navigation Component** (`src/components/Navigation.tsx`)
- Modern glassmorphism effect with backdrop blur
- Gradient logo and branding
- Active state highlighting with gradient backgrounds
- Smooth hover transitions
- Fully responsive design

### 2. **Dashboard** (`src/app/page.tsx`)
- Hero section with gradient headings
- 3 Stats cards showing:
  - Active Goal status and preview
  - Total Sources count (active/total)
  - Latest Digest information
- Quick action cards for:
  - Create Goal
  - Add Source
  - View Digests
- Loading states with spinners
- Smooth animations and hover effects

### 3. **Goals Management** (`src/app/goals/page.tsx`)
- Display current active goal with:
  - Goal text
  - Difficulty level badge
  - Frequency badge
  - Creation date
- Form to create/update goals:
  - Goal text textarea
  - Difficulty level selector (beginner/intermediate/advanced)
  - Frequency selector (daily/weekly/biweekly)
- Beautiful gradient card designs
- Loading and submitting states

### 4. **Sources Management** (`src/app/sources/page.tsx`)
- Quick seed default RSS feeds button
- Custom source form with:
  - Source type selector (RSS, YouTube, Reddit, X/Twitter, Website)
  - Source URL/identifier input
- Grid display of all sources:
  - Source type icons
  - Status badges (Active/Disabled/Error)
  - Source URL display
  - Created and last fetched dates
- Modern card grid layout
- Empty state with call-to-action

### 5. **Digests Viewer** (`src/app/digests/page.tsx`)
- List view of all digests showing:
  - Goal text preview
  - Date range (week_start_date - week_end_date)
  - Total items count
  - Generation date
- Detailed digest view with:
  - Full goal text
  - Date range and generation info
  - All digest items with:
    - Item number
    - Title
    - Summary section
    - "Why It Matters" section
    - Relevance score
    - Source type badge
    - External link
    - Feedback buttons (useful/not useful)
- Back to list navigation
- Click-to-expand functionality
- Feedback submission with visual confirmation

## Design Elements

### Color Palette
- **Primary Gradients:**
  - Blue to Indigo to Purple (`from-blue-600 via-indigo-600 to-purple-600`)
  - Purple to Pink to Red (`from-purple-600 via-pink-600 to-red-600`)
  - Pink to Red to Orange (`from-pink-600 via-red-600 to-orange-600`)

### Background
- Gradient background: `bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100`

### UI Components
- Glassmorphism navigation with `backdrop-blur-lg`
- Card designs with shadows and hover effects
- Gradient backgrounds with blur effects for depth
- Smooth transitions and scale animations on hover
- Custom scrollbar with gradient styling

### Typography
- Inter font family (Google Fonts)
- Gradient text effects using `bg-clip-text`
- Clear hierarchy with varied font sizes

## API Integration

The frontend uses the API client (`src/lib/api.ts`) which includes:

### Goals API
- `getActiveGoal()` - Fetch current active goal
- `createGoal(goalText, difficultyLevel, frequency)` - Create new goal

### Sources API
- `getSources()` - Fetch all sources
- `addSource(sourceType, value)` - Add new source
- `seedDefaultSources()` - Add default RSS feeds
- `updateSourceStatus(sourceId, status)` - Update source status

### Digests API
- `getCurrentDigest()` - Get latest digest
- `getDigestHistory(limit, offset)` - Get digest history
- `getDigestById(digestId)` - Get specific digest with items
- `submitFeedback(digestItemId, contentId, feedbackValue)` - Submit item feedback

## Running the Frontend

```bash
# Install dependencies (if not already done)
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The frontend will run on `http://localhost:3000` and connect to the backend API at `http://localhost:8000`.

## Environment Variables

Create a `.env.local` file with:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USER_ID=test-user
```

## File Structure

```
src/
├── app/
│   ├── page.tsx                 # Dashboard
│   ├── layout.tsx               # Root layout with Inter font
│   ├── globals.css              # Global styles with animations
│   ├── goals/
│   │   └── page.tsx            # Goals management
│   ├── sources/
│   │   └── page.tsx            # Sources management
│   └── digests/
│       └── page.tsx            # Digests viewer
├── components/
│   └── Navigation.tsx           # Navigation component
└── lib/
    └── api.ts                   # API client functions
```

## Features & UX

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Loading States**: Spinners and skeleton screens
- **Error Handling**: User-friendly error messages
- **Optimistic Updates**: Immediate UI feedback
- **Smooth Animations**: Fade-ins, scale transforms, and transitions
- **Accessibility**: Semantic HTML and ARIA attributes
- **Modern UI**: Gradients, shadows, and glassmorphism effects

## Next Steps

1. Add authentication and user management
2. Implement real-time updates with WebSockets
3. Add digest generation trigger UI
4. Create settings page for user preferences
5. Add analytics dashboard
6. Implement search and filtering
7. Add dark mode support
8. Create mobile app with React Native

## Technologies Used

- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **Inter Font** - Modern typography
- **Fetch API** - HTTP requests

Built with modern web standards and best practices for performance and user experience.
