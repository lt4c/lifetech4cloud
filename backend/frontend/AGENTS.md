# React Bits

React Bits is an extensive library of animated React components designed to help developers create visually striking web applications. The library provides over 110 production-ready components spanning four main categories: text animations, interactive animations, UI components, and animated backgrounds. Each component is built with minimal dependencies and offers extensive customization through props, making it easy to integrate sophisticated animations into any React project without starting from scratch.

The library stands out for its comprehensive offering of component variants tailored to different tech stacks. Every component is available in four distinct flavors: JavaScript with CSS (JS-CSS), JavaScript with Tailwind (JS-TW), TypeScript with CSS (TS-CSS), and TypeScript with Tailwind (TS-TW). This flexibility ensures that developers can use the components regardless of their preferred styling approach or type system. Components leverage modern animation libraries like Motion (formerly Framer Motion), GSAP, and WebGL through OGL for high-performance rendering, while maintaining a clean API surface that abstracts away complexity.

## Installation and Component Integration

### Manual Installation via Copy-Paste

Manual installation involves copying component code directly from the documentation website and installing required dependencies manually.

```bash
# Step 1: Install dependencies for your chosen component (example: BlobCursor uses gsap)
npm install gsap

# Step 2: Create the component file in your project
touch src/components/BlobCursor/BlobCursor.jsx

# Step 3: Copy the component code from reactbits.dev and paste it into your file
# Step 4: Import and use the component in your application
```

```jsx
// Example usage after manual installation
import BlobCursor from './components/BlobCursor/BlobCursor';

function App() {
  return (
    <div className="app">
      <BlobCursor
        blobType="circle"
        fillColor="#5227FF"
        trailCount={3}
        sizes={[60, 125, 75]}
      />
      <h1>My Application</h1>
    </div>
  );
}
```

### CLI Installation via shadcn

React Bits supports shadcn CLI for rapid component installation with automatic dependency resolution and file placement.

```bash
# Initialize shadcn in your project (if not already set up)
npx shadcn@latest init

# Install a specific component variant using shadcn
# Format: ComponentName-LANG-STYLE
# LANG: JS or TS
# STYLE: CSS or TW (Tailwind)

npx shadcn@latest add https://reactbits.dev/r/BlurText-JS-TW.json

# The component is automatically installed to the correct location
# Dependencies are added to package.json
# You can immediately import and use it
```

```jsx
// Immediate usage after shadcn installation
import BlurText from '@/components/ui/BlurText';

export default function HomePage() {
  return (
    <BlurText
      text="Welcome to the future of web design"
      delay={200}
      animateBy="words"
      direction="top"
      className="text-4xl font-bold"
    />
  );
}
```

### CLI Installation via jsrepo

jsrepo provides another CLI option for component installation with similar benefits to shadcn.

```bash
# Install a component using jsrepo CLI
npx jsrepo add reactbits/BlurText-JS-TW

# Or install from the full registry URL
npx jsrepo add https://reactbits.dev/r/BlurText-JS-TW.json

# jsrepo handles dependency installation and file creation automatically
```

## Text Animation Components

### BlurText Component

BlurText creates a progressive blur-to-focus reveal animation for text content, with support for word-by-word or character-by-character animation triggered by viewport intersection.

```jsx
import BlurText from './BlurText';

// Basic usage with default settings
export default function Hero() {
  return (
    <div className="hero-section">
      <BlurText
        text="Transform your user experience"
        delay={150}
        className="text-6xl font-black text-white"
      />
    </div>
  );
}

// Advanced usage with custom animation stages and callbacks
export default function AnimatedSection() {
  const handleComplete = () => {
    console.log('Animation completed!');
  };

  return (
    <BlurText
      text="Multi-stage animation example"
      delay={100}
      animateBy="characters"
      direction="bottom"
      threshold={0.3}
      rootMargin="0px 0px -100px 0px"
      stepDuration={0.4}
      animationFrom={{ filter: 'blur(20px)', opacity: 0, y: 100, scale: 0.8 }}
      animationTo={[
        { filter: 'blur(10px)', opacity: 0.3, y: 50, scale: 0.9 },
        { filter: 'blur(5px)', opacity: 0.7, y: 10, scale: 1 },
        { filter: 'blur(0px)', opacity: 1, y: 0, scale: 1 }
      ]}
      easing={(t) => t * t * (3 - 2 * t)} // Smoothstep easing
      onAnimationComplete={handleComplete}
      className="text-3xl text-center"
    />
  );
}
```

### CountUp Component

CountUp animates numbers from a start value to an end value with configurable duration, formatting, and viewport-based triggering.

```jsx
import CountUp from './CountUp';

// Simple counter for statistics display
export default function Statistics() {
  return (
    <div className="stats-grid">
      <div className="stat-item">
        <CountUp
          end={10000}
          duration={2}
          className="text-5xl font-bold text-purple-600"
        />
        <p>Happy Customers</p>
      </div>

      <div className="stat-item">
        <CountUp
          end={99.9}
          duration={2.5}
          decimals={1}
          suffix="%"
          className="text-5xl font-bold text-green-600"
        />
        <p>Uptime</p>
      </div>

      <div className="stat-item">
        <CountUp
          start={0}
          end={1000000}
          duration={3}
          separator=","
          prefix="$"
          className="text-5xl font-bold text-blue-600"
        />
        <p>Revenue Generated</p>
      </div>
    </div>
  );
}

// Viewport-triggered counter with custom threshold
export default function ScrollTriggeredCounter() {
  return (
    <section style={{ marginTop: '200vh' }}>
      <CountUp
        end={5000}
        duration={1.5}
        threshold={0.5}
        rootMargin="-50px"
        className="text-7xl font-black"
      />
    </section>
  );
}
```

### CircularText Component

CircularText arranges text along a circular path with optional rotation animation.

```jsx
import CircularText from './CircularText';

// Basic circular text
export default function Logo() {
  return (
    <CircularText
      text="REACT BITS • REACT BITS • REACT BITS • "
      radius={100}
      fontSize={16}
      className="circular-logo"
    />
  );
}

// Rotating circular text with custom styling
export default function AnimatedBadge() {
  return (
    <div className="badge-container">
      <CircularText
        text="★ NEW FEATURE ★ AVAILABLE NOW ★ "
        radius={80}
        fontSize={14}
        rotateText={true}
        rotationSpeed={0.5}
        direction="clockwise"
        className="text-yellow-400 font-bold"
      />
      <div className="badge-center">
        <span>NEW</span>
      </div>
    </div>
  );
}
```

## Interactive Animation Components

### BlobCursor Component

BlobCursor creates a trailing blob effect that follows the cursor with customizable shapes, colors, and motion physics powered by GSAP.

```jsx
import BlobCursor from './BlobCursor';

// Basic blob cursor with default settings
export default function App() {
  return (
    <>
      <BlobCursor />
      <main>
        {/* Your application content */}
      </main>
    </>
  );
}

// Advanced customization with multiple trailing blobs
export default function CustomBlobApp() {
  return (
    <>
      <BlobCursor
        blobType="circle"
        fillColor="#FF6B6B"
        trailCount={5}
        sizes={[40, 60, 80, 100, 120]}
        innerSizes={[15, 20, 25, 30, 35]}
        innerColor="rgba(255, 255, 255, 0.9)"
        opacities={[0.8, 0.6, 0.5, 0.4, 0.3]}
        shadowColor="rgba(255, 107, 107, 0.6)"
        shadowBlur={15}
        shadowOffsetX={5}
        shadowOffsetY={5}
        useFilter={true}
        filterStdDeviation={40}
        fastDuration={0.05}
        slowDuration={0.8}
        fastEase="power4.out"
        slowEase="power2.out"
        zIndex={9999}
      />
      <main>
        <h1>Hover around to see the blob effect</h1>
      </main>
    </>
  );
}

// Square blob variant without SVG filter
export default function SquareBlobApp() {
  return (
    <>
      <BlobCursor
        blobType="square"
        fillColor="#4ECDC4"
        trailCount={3}
        sizes={[50, 90, 70]}
        useFilter={false}
        opacities={[0.7, 0.5, 0.3]}
      />
      <main>Content</main>
    </>
  );
}
```

### Magnet Component

Magnet creates a magnetic pull effect on child elements when the cursor approaches, perfect for interactive buttons and cards.

```jsx
import Magnet from './Magnet';

// Basic magnet effect on a button
export default function MagneticButton() {
  return (
    <Magnet>
      <button className="cta-button">
        Click Me
      </button>
    </Magnet>
  );
}

// Customized magnetic pull with stronger attraction
export default function InteractiveCard() {
  return (
    <div className="card-grid">
      <Magnet
        magnitude={0.5}
        maxDistance={200}
        className="magnetic-card"
      >
        <div className="card">
          <h3>Product 1</h3>
          <p>Hover to feel the pull</p>
        </div>
      </Magnet>

      <Magnet
        magnitude={0.3}
        maxDistance={150}
      >
        <div className="card">
          <h3>Product 2</h3>
          <p>Subtle magnetic effect</p>
        </div>
      </Magnet>
    </div>
  );
}

// Magnetic text with custom easing
export default function MagneticHeading() {
  return (
    <Magnet
      magnitude={0.2}
      maxDistance={100}
      damping={20}
      stiffness={150}
    >
      <h1 className="text-7xl font-bold">
        Interactive Heading
      </h1>
    </Magnet>
  );
}
```

### ClickSpark Component

ClickSpark generates particle explosions at click locations with customizable colors and particle behavior.

```jsx
import ClickSpark from './ClickSpark';

// Full-page click sparks with default settings
export default function App() {
  return (
    <>
      <ClickSpark />
      <main>
        <h1>Click anywhere to see sparks!</h1>
      </main>
    </>
  );
}

// Customized spark effect with specific colors and behavior
export default function CustomSparkApp() {
  return (
    <>
      <ClickSpark
        colors={['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']}
        particleCount={30}
        particleSize={8}
        speed={4}
        gravity={0.8}
        fadeSpeed={0.98}
        className="spark-layer"
      />
      <main>Content</main>
    </>
  );
}

// Confined spark effect within a specific container
export default function ContainedSparks() {
  return (
    <div className="interactive-section" style={{ position: 'relative' }}>
      <ClickSpark
        colors={['#FFD700', '#FFA500']}
        particleCount={20}
        containerSelector=".interactive-section"
      />
      <div className="content">
        Click inside this section for sparks!
      </div>
    </div>
  );
}
```

## UI Components

### Dock Component

Dock creates a macOS-style application dock with magnification effects and smooth spring animations powered by Motion.

```jsx
import Dock from './Dock';
import { VscHome, VscArchive, VscAccount, VscSettingsGear } from 'react-icons/vsc';

// Basic dock with icon navigation
export default function AppDock() {
  const items = [
    {
      icon: <VscHome size={24} />,
      label: 'Home',
      onClick: () => console.log('Home clicked')
    },
    {
      icon: <VscArchive size={24} />,
      label: 'Archive',
      onClick: () => console.log('Archive clicked')
    },
    {
      icon: <VscAccount size={24} />,
      label: 'Profile',
      onClick: () => console.log('Profile clicked')
    },
    {
      icon: <VscSettingsGear size={24} />,
      label: 'Settings',
      onClick: () => console.log('Settings clicked')
    }
  ];

  return (
    <div className="dock-container">
      <Dock items={items} />
    </div>
  );
}

// Customized dock with routing integration
export default function NavigationDock() {
  const navigate = useNavigate();

  const dockItems = [
    {
      icon: <HomeIcon />,
      label: 'Dashboard',
      onClick: () => navigate('/dashboard'),
      className: 'dock-item-primary'
    },
    {
      icon: <FolderIcon />,
      label: 'Projects',
      onClick: () => navigate('/projects')
    },
    {
      icon: <MessageIcon />,
      label: 'Messages',
      onClick: () => navigate('/messages')
    },
    {
      icon: <UserIcon />,
      label: 'Profile',
      onClick: () => navigate('/profile')
    }
  ];

  return (
    <Dock
      items={dockItems}
      className="custom-dock"
      spring={{ mass: 0.15, stiffness: 200, damping: 15 }}
      magnification={80}
      distance={250}
      panelHeight={70}
      baseItemSize={55}
      dockHeight={300}
    />
  );
}

// Minimal dock with subtle effects
export default function MinimalDock() {
  const tools = [
    { icon: <PenIcon />, label: 'Draw', onClick: () => {} },
    { icon: <EraserIcon />, label: 'Erase', onClick: () => {} },
    { icon: <ShapesIcon />, label: 'Shapes', onClick: () => {} },
    { icon: <TextIcon />, label: 'Text', onClick: () => {} }
  ];

  return (
    <Dock
      items={tools}
      magnification={60}
      distance={150}
      panelHeight={50}
      baseItemSize={40}
      spring={{ mass: 0.1, stiffness: 180, damping: 14 }}
    />
  );
}
```

### Stepper Component

Stepper provides a multi-step form interface with animated transitions, progress indicators, and customizable navigation controls.

```jsx
import Stepper, { Step } from './Stepper';

// Basic stepper for onboarding flow
export default function OnboardingFlow() {
  const handleStepChange = (step) => {
    console.log('Current step:', step);
  };

  const handleComplete = () => {
    console.log('Onboarding completed!');
  };

  return (
    <Stepper
      initialStep={1}
      onStepChange={handleStepChange}
      onFinalStepCompleted={handleComplete}
    >
      <Step>
        <h2>Welcome!</h2>
        <p>Let's get you set up in just a few steps.</p>
      </Step>

      <Step>
        <h2>Profile Information</h2>
        <input type="text" placeholder="Name" />
        <input type="email" placeholder="Email" />
      </Step>

      <Step>
        <h2>Preferences</h2>
        <label>
          <input type="checkbox" /> Enable notifications
        </label>
        <label>
          <input type="checkbox" /> Dark mode
        </label>
      </Step>

      <Step>
        <h2>All Set!</h2>
        <p>You're ready to start using the platform.</p>
      </Step>
    </Stepper>
  );
}

// Advanced stepper with custom styling and controls
export default function CustomStepper() {
  const [currentStep, setCurrentStep] = useState(1);

  return (
    <Stepper
      initialStep={currentStep}
      onStepChange={setCurrentStep}
      onFinalStepCompleted={() => alert('Process complete!')}
      stepCircleContainerClassName="custom-stepper-container"
      stepContainerClassName="custom-indicators"
      contentClassName="custom-content"
      footerClassName="custom-footer"
      backButtonText="Previous"
      nextButtonText="Next Step"
      backButtonProps={{ className: 'btn-secondary' }}
      nextButtonProps={{ className: 'btn-primary' }}
    >
      <Step>
        <div className="step-content">
          <h3>Step 1: Basic Info</h3>
          <form>
            <input type="text" placeholder="Company Name" />
            <input type="text" placeholder="Industry" />
          </form>
        </div>
      </Step>

      <Step>
        <div className="step-content">
          <h3>Step 2: Team Size</h3>
          <select>
            <option>1-10 employees</option>
            <option>11-50 employees</option>
            <option>51+ employees</option>
          </select>
        </div>
      </Step>

      <Step>
        <div className="step-content">
          <h3>Step 3: Confirmation</h3>
          <p>Review your information and click Complete.</p>
        </div>
      </Step>
    </Stepper>
  );
}

// Stepper with custom step indicators
export default function CustomIndicatorStepper() {
  const renderCustomIndicator = ({ step, currentStep, onStepClick }) => {
    const isActive = step === currentStep;
    const isComplete = step < currentStep;

    return (
      <button
        className={`custom-indicator ${isActive ? 'active' : ''} ${isComplete ? 'complete' : ''}`}
        onClick={() => onStepClick(step)}
      >
        {isComplete ? '✓' : step}
      </button>
    );
  };

  return (
    <Stepper
      renderStepIndicator={renderCustomIndicator}
      disableStepIndicators={false}
    >
      <Step><div>Content 1</div></Step>
      <Step><div>Content 2</div></Step>
      <Step><div>Content 3</div></Step>
    </Stepper>
  );
}
```

### AnimatedList Component

AnimatedList renders items with staggered entrance animations, supporting dynamic additions and removals.

```jsx
import AnimatedList from './AnimatedList';

// Basic animated notification list
export default function NotificationFeed() {
  const notifications = [
    { id: 1, text: 'New message from John', time: '2m ago' },
    { id: 2, text: 'Your report is ready', time: '5m ago' },
    { id: 3, text: 'Meeting in 30 minutes', time: '15m ago' }
  ];

  return (
    <AnimatedList className="notification-list">
      {notifications.map((notif) => (
        <div key={notif.id} className="notification-item">
          <p>{notif.text}</p>
          <span>{notif.time}</span>
        </div>
      ))}
    </AnimatedList>
  );
}

// Dynamic list with add/remove functionality
export default function TodoList() {
  const [todos, setTodos] = useState([
    { id: 1, text: 'Review pull requests' },
    { id: 2, text: 'Update documentation' }
  ]);

  const addTodo = (text) => {
    const newTodo = { id: Date.now(), text };
    setTodos([...todos, newTodo]);
  };

  const removeTodo = (id) => {
    setTodos(todos.filter(t => t.id !== id));
  };

  return (
    <div>
      <input
        type="text"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && e.target.value) {
            addTodo(e.target.value);
            e.target.value = '';
          }
        }}
        placeholder="Add todo..."
      />

      <AnimatedList
        stagger={0.1}
        duration={0.4}
        className="todo-list"
      >
        {todos.map((todo) => (
          <div key={todo.id} className="todo-item">
            <span>{todo.text}</span>
            <button onClick={() => removeTodo(todo.id)}>✕</button>
          </div>
        ))}
      </AnimatedList>
    </div>
  );
}

// Custom animation variants
export default function CustomAnimatedList() {
  const items = ['Item 1', 'Item 2', 'Item 3', 'Item 4'];

  return (
    <AnimatedList
      stagger={0.15}
      duration={0.6}
      initial={{ opacity: 0, x: -50, scale: 0.8 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 50, scale: 0.8 }}
      className="custom-list"
    >
      {items.map((item, i) => (
        <div key={i} className="list-item">{item}</div>
      ))}
    </AnimatedList>
  );
}
```

## Background Components

### Particles Component

Particles creates a WebGL-powered 3D particle system with customizable colors, motion, and interactive hover effects using the OGL library.

```jsx
import Particles from './Particles';

// Basic particle background
export default function HeroSection() {
  return (
    <section className="hero" style={{ position: 'relative', height: '100vh' }}>
      <Particles className="particles-bg" />
      <div className="hero-content">
        <h1>Welcome to the Future</h1>
        <p>Experience immersive particle effects</p>
      </div>
    </section>
  );
}

// Customized particles with brand colors
export default function BrandedParticles() {
  const brandColors = ['#FF6B6B', '#4ECDC4', '#45B7D1'];

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <Particles
        particleCount={300}
        particleColors={brandColors}
        particleSpread={12}
        speed={0.15}
        particleBaseSize={120}
        sizeRandomness={1.5}
        alphaParticles={true}
        cameraDistance={25}
        className="brand-particles"
      />
      <main>Content overlays the particles</main>
    </div>
  );
}

// Interactive particles that respond to mouse movement
export default function InteractiveParticles() {
  return (
    <section style={{ position: 'relative', height: '80vh' }}>
      <Particles
        particleCount={150}
        particleColors={['#FFD700', '#FFA500', '#FF8C00']}
        particleSpread={8}
        speed={0.08}
        moveParticlesOnHover={true}
        particleHoverFactor={2}
        disableRotation={false}
        particleBaseSize={80}
        sizeRandomness={0.8}
        alphaParticles={false}
        cameraDistance={18}
      />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <h1>Move your mouse to interact</h1>
      </div>
    </section>
  );
}

// Minimal particle effect with static rotation disabled
export default function StaticParticles() {
  return (
    <Particles
      particleCount={100}
      particleColors={['#FFFFFF']}
      particleSpread={15}
      speed={0.05}
      disableRotation={true}
      particleBaseSize={100}
      sizeRandomness={0}
      alphaParticles={true}
      cameraDistance={30}
    />
  );
}
```

### Aurora Component

Aurora generates dynamic gradient backgrounds with animated color shifts reminiscent of the northern lights.

```jsx
import Aurora from './Aurora';

// Basic aurora background
export default function LandingPage() {
  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <Aurora />
      <main style={{ position: 'relative', zIndex: 1 }}>
        <h1>Beautiful Aurora Background</h1>
      </main>
    </div>
  );
}

// Customized aurora with specific colors
export default function CustomAurora() {
  return (
    <>
      <Aurora
        colors={['#FF00FF', '#00FFFF', '#FFFF00']}
        speed={0.5}
        blur={80}
        className="custom-aurora"
      />
      <div className="content">
        Cyberpunk-themed aurora effect
      </div>
    </>
  );
}

// Subtle aurora for professional sites
export default function ProfessionalAurora() {
  return (
    <>
      <Aurora
        colors={['#E0E7FF', '#DBEAFE', '#E0F2FE']}
        speed={0.2}
        blur={120}
        opacity={0.4}
      />
      <main>Professional content with subtle animated background</main>
    </>
  );
}
```

### Plasma Component

Plasma creates organic, flowing plasma effects using WebGL shaders for performance-intensive animated backgrounds.

```jsx
import Plasma from './Plasma';

// Default plasma effect
export default function PlasmaBackground() {
  return (
    <div className="section" style={{ position: 'relative', height: '100vh' }}>
      <Plasma />
      <div className="overlay-content">
        <h1>Plasma Background</h1>
      </div>
    </div>
  );
}

// Customized plasma colors and animation speed
export default function CustomPlasma() {
  return (
    <Plasma
      color1="#FF0080"
      color2="#7928CA"
      color3="#00DFD8"
      speed={0.8}
      blur={30}
      className="plasma-bg"
    />
  );
}

// Slow, meditative plasma for zen interfaces
export default function ZenPlasma() {
  return (
    <Plasma
      color1="#9D7CBF"
      color2="#8FB9AA"
      color3="#FDB750"
      speed={0.3}
      blur={50}
    />
  );
}
```

## Component Registry and Build System

### Registry Structure

React Bits uses a JSON-based registry system compatible with shadcn CLI for distributing components.

```json
{
  "$schema": "https://ui.shadcn.com/schema/registry-item.json",
  "name": "BlurText-JS-TW",
  "type": "registry:block",
  "title": "BlurText",
  "description": "Text starts blurred then crisply resolves for a soft-focus reveal effect.",
  "dependencies": [
    "motion"
  ],
  "files": [
    {
      "path": "public/tailwind/src/tailwind/TextAnimations/BlurText/BlurText.jsx",
      "content": "import { motion } from 'motion/react';\n...",
      "type": "registry:component"
    }
  ]
}
```

```bash
# Generate registry files for all component variants
npm run shadcn:generate

# This script processes all components from:
# - src/content (JS-CSS variant)
# - src/tailwind (JS-TW variant)
# - src/ts-default (TS-CSS variant)
# - src/ts-tailwind (TS-TW variant)

# Output locations:
# - public/r/*.json (shadcn registry files)
# - public/default/ (jsrepo JS-CSS builds)
# - public/tailwind/ (jsrepo JS-TW builds)
# - public/ts/default/ (jsrepo TS-CSS builds)
# - public/ts/tailwind/ (jsrepo TS-TW builds)
```

### Project Scripts

Build process for generating all component variants and registries.

```bash
# Full production build
npm run build
# Executes: jsrepo:build && shadcn:build && llms:text && vite build

# Build individual variant registries in parallel
npm run jsrepo:build
# Runs concurrently:
# - jsrepo build --dirs ./src/content --output-dir ./public/default
# - jsrepo build --dirs ./src/tailwind --output-dir ./public/tailwind
# - jsrepo build --dirs ./src/ts-default --output-dir ./public/ts/default
# - jsrepo build --dirs ./src/ts-tailwind --output-dir ./public/ts/tailwind

# Generate shadcn-compatible registry
npm run shadcn:build
# Executes: shadcn:generate && shadcn build

# Create new component with scaffolding
npm run new:component
# Runs: node scripts/generateComponent.js
# Prompts for component details and creates template files

# Development server with HMR
npm run dev
# Starts Vite dev server with hot module replacement

# Format all code
npm run format
# Runs Prettier on the entire codebase
```

### Component Development Workflow

Creating a new component following the React Bits structure.

```bash
# Step 1: Generate component scaffolding
npm run new:component

# Script will prompt for:
# - Component name (e.g., "MagicButton")
# - Category (TextAnimations, Animations, Components, Backgrounds)
# - Description

# This creates:
# - src/content/[Category]/[Name]/[Name].jsx (JS-CSS variant)
# - src/tailwind/[Category]/[Name]/[Name].jsx (JS-TW variant)
# - src/ts-default/[Category]/[Name]/[Name].tsx (TS-CSS variant)
# - src/ts-tailwind/[Category]/[Name]/[Name].tsx (TS-TW variant)
# - src/demo/[Category]/[Name]Demo.jsx (demo component)
# - src/constants/code/[Category]/[name]Code.js (code examples)
```

```javascript
// Example generated component structure (src/content/Components/MagicButton/MagicButton.jsx)
import { useState } from 'react';
import './MagicButton.css';

export default function MagicButton({
  children,
  onClick,
  variant = 'primary',
  className = '',
  ...rest
}) {
  return (
    <button
      className={`magic-button magic-button-${variant} ${className}`}
      onClick={onClick}
      {...rest}
    >
      {children}
    </button>
  );
}
```

```javascript
// Corresponding demo component (src/demo/Components/MagicButtonDemo.jsx)
import { useState } from 'react';
import { Box } from '@chakra-ui/react';
import { CodeTab, PreviewTab, TabsLayout } from '../../components/common/TabsLayout';
import Customize from '../../components/common/Preview/Customize';
import PreviewSelect from '../../components/common/Preview/PreviewSelect';
import CodeExample from '../../components/code/CodeExample';
import PropTable from '../../components/common/Preview/PropTable';

import MagicButton from '../../content/Components/MagicButton/MagicButton';
import { magicButton } from '../../constants/code/Components/magicButtonCode';

export default function MagicButtonDemo() {
  const [variant, setVariant] = useState('primary');

  const propData = [
    {
      name: 'children',
      type: 'ReactNode',
      default: '-',
      description: 'Button content'
    },
    {
      name: 'variant',
      type: '"primary" | "secondary" | "ghost"',
      default: '"primary"',
      description: 'Visual style variant'
    },
    {
      name: 'onClick',
      type: '() => void',
      default: '-',
      description: 'Click handler function'
    }
  ];

  return (
    <TabsLayout>
      <PreviewTab>
        <Box className="demo-container" minH={400}>
          <MagicButton variant={variant} onClick={() => alert('Clicked!')}>
            Click Me
          </MagicButton>
        </Box>

        <Customize>
          <PreviewSelect
            title="Variant"
            value={variant}
            options={['primary', 'secondary', 'ghost']}
            onChange={setVariant}
          />
        </Customize>

        <PropTable data={propData} />
      </PreviewTab>

      <CodeTab>
        <CodeExample codeObject={magicButton} />
      </CodeTab>
    </TabsLayout>
  );
}
```

## Summary and Integration Patterns

React Bits serves as a comprehensive solution for developers seeking to elevate their React applications with professional-grade animations and interactive components. The library's primary use cases span landing pages requiring eye-catching hero sections with particle backgrounds and text animations, dashboard applications needing smooth transitions and micro-interactions, marketing sites demanding attention-grabbing visual effects, portfolio websites showcasing creative capabilities, and product demos that require polished, production-ready components. The component-first architecture means developers can cherry-pick exactly what they need rather than importing an entire library, keeping bundle sizes minimal while maximizing visual impact.

Integration patterns follow modern React best practices with support for both controlled and uncontrolled component states, comprehensive prop-based customization, and compatibility with popular styling solutions including CSS Modules, Tailwind CSS, and CSS-in-JS. Components are designed to be framework-agnostic within the React ecosystem, working seamlessly with Next.js, Remix, Vite, and Create React App. The multi-CLI installation approach (manual, shadcn, jsrepo) ensures developers can adopt components using their preferred workflow. Advanced users can extend components by forking the source code and modifying animation parameters, shader code, or adding new variants. The build system generates four variants per component automatically, demonstrating a scalable approach to maintaining consistency across different tech stack preferences while maximizing developer flexibility.

# shadcn/ui

shadcn/ui is a collection of accessible and customizable UI components built with React, Radix UI, and Tailwind CSS. Unlike traditional component libraries, shadcn/ui provides a CLI tool that copies component source code directly into your project, giving you full ownership and customization control. The components are not installed as dependencies but rather integrated into your codebase where you can modify them freely.

The project is structured as a monorepo containing the shadcn CLI package, documentation website, component registry, and example implementations. The CLI (`npx shadcn`) handles project initialization, component installation, dependency management, and configuration updates. Components are stored in a registry system organized by style variants (default, new-york) and fetched dynamically during installation. The system supports custom registries, allowing teams to create and maintain their own component collections with private or public access.

## CLI Commands

### Initialize a new project

```bash
# Initialize with interactive prompts
npx shadcn init

# Initialize with defaults (Next.js, TypeScript, neutral base color)
npx shadcn init --defaults

# Initialize with specific configuration
npx shadcn init --base-color slate --no-css-variables --template next

# Initialize and add components in one command
npx shadcn init button card dialog
```

### Add components to your project

```bash
# Add a single component
npx shadcn add button

# Add multiple components
npx shadcn add button card dialog

# Add all available components
npx shadcn add --all

# Add component with overwrite
npx shadcn add button --overwrite

# Add component from URL or registry
npx shadcn add https://example.com/button.json
npx shadcn add @acme/button

# Skip confirmation prompts
npx shadcn add button --yes
```

### Check for component updates

```bash
# Check all components for updates
npx shadcn diff

# Check specific component for updates
npx shadcn diff button

# Example output when updates are found:
# The following components have updates available:
# - button
#   - components/ui/button.tsx
# Run diff <component> to see the changes.
```

### Search for components

```bash
# Search components interactively
npx shadcn search

# Search for specific term
npx shadcn search dialog

# Example: Search returns component names, descriptions, and categories
# Results are fuzzy-matched and ranked by relevance
```

### View component information

```bash
# View component details
npx shadcn view button

# Example output includes:
# - Component name and description
# - Dependencies (npm packages)
# - Registry dependencies (other shadcn components)
# - Files that will be installed
# - Tailwind configuration requirements
```

### Project information

```bash
# Display project configuration
npx shadcn info

# Example output:
# Project: my-app
# Framework: Next.js
# Style: new-york
# TypeScript: Yes
# Tailwind CSS: 3.4.6
# CSS Variables: Yes
```

### Run migrations

```bash
# List available migrations
npx shadcn migrate --list

# Run icon library migration
npx shadcn migrate icons

# Run Radix UI migration
npx shadcn migrate radix

# Skip confirmation prompt
npx shadcn migrate icons --yes

# Available migrations:
# - icons: Migrate your UI components to a different icon library
# - radix: Migrate to radix-ui
```

### Build registry

```bash
# Build components for a shadcn registry
npx shadcn build

# Build with custom registry file
npx shadcn build ./my-registry.json

# Specify output directory
npx shadcn build --output ./dist/r

# Example: Build registry from registry.json to public/r
npx shadcn build ./registry.json --output ./public/r
```

## Registry API

### Fetch registry items programmatically

```typescript
import { getRegistryItems } from "shadcn/registry"

// Fetch single component
const [button] = await getRegistryItems(["button"], {
  config: {
    style: "new-york",
    tailwind: {
      config: "tailwind.config.js",
      css: "app/globals.css",
      baseColor: "slate",
      cssVariables: true,
    },
  },
})

// Access component metadata
console.log(button.name) // "button"
console.log(button.type) // "registry:ui"
console.log(button.dependencies) // ["@radix-ui/react-slot"]
console.log(button.files) // [{ path: "button.tsx", content: "...", type: "registry:ui" }]

// Fetch multiple components
const items = await getRegistryItems(["button", "card", "dialog"])
items.forEach((item) => {
  console.log(`${item.name}: ${item.files?.length} files`)
})
```

### Resolve component dependency tree

```typescript
import { resolveRegistryItems } from "shadcn/registry"

// Resolve all dependencies for a component
const tree = await resolveRegistryItems(["dialog"], {
  config: {
    style: "new-york",
  },
})

// tree contains the dialog component plus all its dependencies
// For example, dialog might depend on button, which is automatically included
console.log(tree.files) // All files needed for dialog and its dependencies
console.log(tree.dependencies) // ["@radix-ui/react-dialog", "@radix-ui/react-slot"]
console.log(tree.registryDependencies) // ["button"]
```

### Fetch registry configuration

```typescript
import { getRegistry, getRegistriesConfig, getRegistriesIndex } from "shadcn/registry"

// Fetch registry metadata
const registry = await getRegistry("@shadcn/ui")

console.log(registry.name) // "@shadcn/ui"
console.log(registry.homepage) // "https://ui.shadcn.com"
console.log(registry.items.length) // Number of available components

// Access built-in and custom registries from local config
const config = await getRegistriesConfig(process.cwd())
console.log(config.registries) // { "@shadcn": {...}, "@acme": {...} }

// Fetch global registries index from shadcn registry
const registriesIndex = await getRegistriesIndex()
registriesIndex.forEach((registry) => {
  console.log(`${registry.name} - ${registry.description}`)
  console.log(`URL: ${registry.url}`)
})
```

### Fetch registry index and styles

```typescript
import {
  getShadcnRegistryIndex,
  getRegistryStyles,
  getRegistryBaseColors,
  getRegistryIcons,
} from "shadcn/registry"

// Get all available components
const index = await getShadcnRegistryIndex()
index.forEach((item) => {
  console.log(`${item.name} - ${item.description}`)
})

// Get available styles
const styles = await getRegistryStyles()
// Returns: [{ name: "default", label: "Default" }, { name: "new-york", label: "New York" }]

// Get available base colors
const colors = await getRegistryBaseColors()
// Returns: [{ name: "slate", label: "Slate" }, { name: "gray", label: "Gray" }, ...]

// Get available icon libraries
const icons = await getRegistryIcons()
// Returns icon library configurations for lucide-react, radix-icons, etc.
```

### Search registries programmatically

```typescript
import { searchRegistries } from "shadcn/registry"

// Search for components across registries
const results = await searchRegistries({
  query: "dialog",
  registries: ["@shadcn/ui"],
})

results.forEach((result) => {
  console.log(`${result.name} - ${result.description}`)
  console.log(`Registry: ${result.registry}`)
  console.log(`Type: ${result.type}`)
})

// Search returns fuzzy-matched results ranked by relevance
// Useful for building search interfaces or CLI tools
```

## Component Schema

### Registry item structure

```typescript
import { z } from "zod"
import { registryItemSchema } from "shadcn/schema"

// Define a custom component for your registry
const myComponent: z.infer<typeof registryItemSchema> = {
  name: "my-button",
  type: "registry:ui",
  description: "A customized button component",
  dependencies: ["@radix-ui/react-slot", "class-variance-authority"],
  registryDependencies: ["utils"],
  files: [
    {
      path: "my-button.tsx",
      type: "registry:ui",
      content: `
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        destructive: "bg-destructive text-destructive-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
`,
    },
  ],
  tailwind: {
    config: {
      theme: {
        extend: {
          colors: {
            primary: "hsl(var(--primary))",
            "primary-foreground": "hsl(var(--primary-foreground))",
          },
        },
      },
    },
  },
  cssVars: {
    light: {
      primary: "222.2 47.4% 11.2%",
      "primary-foreground": "210 40% 98%",
    },
    dark: {
      primary: "210 40% 98%",
      "primary-foreground": "222.2 47.4% 11.2%",
    },
  },
}

// Validate against schema
registryItemSchema.parse(myComponent)
```

### Custom registry configuration

```typescript
import { promises as fs } from "fs"
import { z } from "zod"

// Define custom registry in components.json
const componentsConfig = {
  $schema: "https://ui.shadcn.com/schema.json",
  style: "new-york",
  rsc: true,
  tsx: true,
  tailwind: {
    config: "tailwind.config.ts",
    css: "app/globals.css",
    baseColor: "slate",
    cssVariables: true,
  },
  aliases: {
    components: "@/components",
    utils: "@/lib/utils",
    lib: "@/lib",
    hooks: "@/hooks",
  },
  registries: {
    "@acme": {
      url: "https://registry.acme.com/{name}.json",
      headers: {
        Authorization: "Bearer ${ACME_TOKEN}",
      },
    },
    "@private": "https://internal.company.com/components/{name}.json",
  },
}

// Write configuration
await fs.writeFile(
  "components.json",
  JSON.stringify(componentsConfig, null, 2)
)

// Now you can install from custom registries:
// npx shadcn add @acme/custom-button
// npx shadcn add @private/internal-component
```

## MCP Server Integration

### Initialize MCP server for AI assistants

```bash
# Initialize MCP server for Claude Code
npx shadcn mcp init --client claude

# Initialize for Cursor
npx shadcn mcp init --client cursor

# Initialize for VS Code
npx shadcn mcp init --client vscode

# This creates configuration files:
# Claude: .mcp.json
# Cursor: .cursor/mcp.json
# VS Code: .vscode/mcp.json

# Example .mcp.json content:
# {
#   "mcpServers": {
#     "shadcn": {
#       "command": "npx",
#       "args": ["shadcn@latest", "mcp"]
#     }
#   }
# }
```

### Run MCP server

```bash
# Start MCP server (used internally by AI assistants)
npx shadcn mcp

# The server provides tools for AI assistants to:
# - List available components
# - Search components
# - Get component details
# - Install components
# - Update components
```

## Programmatic Usage

### Initialize project programmatically

```typescript
import { runInit } from "shadcn"

// Initialize a new project
const config = await runInit({
  cwd: "/path/to/project",
  yes: true,
  defaults: false,
  force: false,
  silent: false,
  isNewProject: true,
  srcDir: true,
  cssVariables: true,
  baseStyle: true,
  baseColor: "slate",
  components: ["button", "card"],
})

console.log("Project initialized with config:")
console.log(config.style) // "new-york"
console.log(config.resolvedPaths.components) // "/path/to/project/src/components"
```

### Add components programmatically

```typescript
import { addComponents } from "shadcn"
import { getConfig } from "shadcn"

// Load existing configuration
const config = await getConfig(process.cwd())

// Add components
await addComponents(["button", "card", "dialog"], config, {
  overwrite: false,
  silent: false,
  isNewProject: false,
})

// Components are now installed in your project with:
// - Component files in components/ui/
// - Dependencies added to package.json
// - Tailwind config updated
// - CSS variables added
```

### Validate configuration

```typescript
import { rawConfigSchema } from "shadcn/schema"
import { promises as fs } from "fs"

// Read and validate components.json
const configFile = await fs.readFile("components.json", "utf8")
const config = JSON.parse(configFile)

try {
  const validated = rawConfigSchema.parse(config)
  console.log("Configuration is valid")
} catch (error) {
  console.error("Invalid configuration:", error.errors)
}
```

## Integration and Extension

shadcn/ui is designed for deep integration into your development workflow. The CLI can be used directly in terminal sessions, integrated into npm scripts for automation, or embedded in custom build tools. All components are installed as source code, allowing teams to modify styling, behavior, and structure without worrying about breaking upstream updates. The diff command helps track changes between your customized components and registry updates.

The registry system supports both public and private registries with authentication via environment variables or headers. Teams can fork the registry structure to create company-specific component libraries while maintaining compatibility with the shadcn CLI. The MCP server integration enables AI assistants to discover, install, and update components autonomously during development sessions. Component schemas are fully typed with Zod, enabling type-safe programmatic access and validation of registry items, making it suitable for building custom tooling around the shadcn ecosystem.

# Tailwind CSS Documentation

Tailwind CSS is a utility-first CSS framework that generates styles by scanning HTML, JavaScript, and template files for class names. It provides a comprehensive design system through CSS utility classes, enabling rapid UI development without writing custom CSS. The framework operates at build-time, analyzing source files and generating only the CSS classes actually used in the project, resulting in optimized production bundles with zero runtime overhead.

The framework includes an extensive default color palette (18 colors with 11 shades each), responsive breakpoint system, customizable design tokens via CSS custom properties, and support for dark mode, pseudo-classes, pseudo-elements, and media queries through variant prefixes. Tailwind CSS v4.1 introduces CSS-first configuration using the `@theme` directive, native support for custom utilities via `@utility`, seamless integration with modern build tools through Vite, PostCSS, and framework-specific plugins, and enhanced arbitrary value syntax for maximum flexibility.

## Installation with Vite

Installing Tailwind CSS using the Vite plugin for modern JavaScript frameworks.

```bash
# Create a new Vite project
npm create vite@latest my-project
cd my-project

# Install Tailwind CSS and Vite plugin
npm install tailwindcss @tailwindcss/vite
```

```javascript
// vite.config.ts
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
})
```

```css
/* src/style.css */
@import "tailwindcss";
```

```html
<!doctype html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="/src/style.css" rel="stylesheet">
</head>
<body>
  <h1 class="text-3xl font-bold underline">
    Hello world!
  </h1>
</body>
</html>
```

## Utility Classes with Variants

Applying conditional styles using variant prefixes for hover, focus, and responsive breakpoints.

```html
<!-- Hover and focus states -->
<button class="bg-sky-500 hover:bg-sky-700 focus:outline-2 focus:outline-offset-2 focus:outline-sky-500 active:bg-sky-800">
  Save changes
</button>

<!-- Responsive breakpoints -->
<div class="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
  <!-- 3 columns on mobile, 4 on tablets, 6 on desktop -->
</div>

<!-- Dark mode support -->
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  Content adapts to color scheme preference
</div>

<!-- Multiple variants stacked -->
<button class="bg-violet-500 hover:bg-violet-600 focus:ring-2 focus:ring-violet-300 disabled:opacity-50 disabled:cursor-not-allowed md:text-lg">
  Submit
</button>
```

## Custom Theme Configuration

Defining custom design tokens using the `@theme` directive in CSS.

```css
/* app.css */
@import "tailwindcss";

@theme {
  /* Custom fonts */
  --font-display: "Satoshi", "sans-serif";
  --font-body: "Inter", system-ui, sans-serif;

  /* Custom colors */
  --color-brand-50: oklch(0.98 0.02 264);
  --color-brand-100: oklch(0.95 0.05 264);
  --color-brand-500: oklch(0.55 0.22 264);
  --color-brand-900: oklch(0.25 0.12 264);

  /* Custom breakpoints */
  --breakpoint-3xl: 120rem;
  --breakpoint-4xl: 160rem;

  /* Custom spacing */
  --spacing-18: calc(var(--spacing) * 18);

  /* Custom animations */
  --ease-fluid: cubic-bezier(0.3, 0, 0, 1);
  --ease-snappy: cubic-bezier(0.2, 0, 0, 1);
}
```

```html
<!-- Using custom theme tokens -->
<div class="font-display text-brand-500 3xl:text-6xl">
  Custom design system
</div>
```

## Arbitrary Values

Using square bracket notation for one-off custom values without leaving HTML.

```html
<!-- Arbitrary property values -->
<div class="top-[117px] lg:top-[344px]">
  Pixel-perfect positioning
</div>

<div class="bg-[#bada55] text-[22px] before:content-['Festivus']">
  Custom hex colors, font sizes, and content
</div>

<!-- Arbitrary properties -->
<div class="[mask-type:luminance] hover:[mask-type:alpha]">
  Any CSS property
</div>

<!-- CSS variables -->
<div class="bg-(--my-brand-color) fill-(--icon-color)">
  Reference custom properties
</div>

<!-- Grid with arbitrary values -->
<div class="grid grid-cols-[1fr_500px_2fr]">
  Complex grid layouts
</div>

<!-- Type hints for ambiguous values -->
<div class="text-(length:--my-var)">
  Font size from CSS variable
</div>
<div class="text-(color:--my-var)">
  Color from CSS variable
</div>
```

## Color System

Working with Tailwind's comprehensive color palette and opacity modifiers.

```html
<!-- Using default color palette -->
<div class="bg-sky-500 border-pink-300 text-gray-950">
  Color utilities across all properties
</div>

<!-- Opacity modifiers -->
<div class="bg-black/75 text-white/90">
  Alpha channel with percentage
</div>

<div class="bg-pink-500/[71.37%]">
  Arbitrary opacity values
</div>

<div class="bg-cyan-400/(--my-alpha-value)">
  Opacity from CSS variable
</div>

<!-- Dark mode color variants -->
<div class="bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700">
  <span class="text-pink-600 dark:text-pink-400">
    Adapts to color scheme
  </span>
</div>

<!-- Color utilities reference -->
<!-- bg-* (background), text-* (text), border-* (border) -->
<!-- decoration-* (text decoration), outline-* (outline) -->
<!-- shadow-* (box shadow), ring-* (ring shadow) -->
<!-- accent-* (form controls), caret-* (text cursor) -->
<!-- fill-* (SVG fill), stroke-* (SVG stroke) -->
```

## Dark Mode

Implementing dark mode with CSS media queries or manual toggle.

```html
<!-- Using prefers-color-scheme (default) -->
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
  <div class="bg-gray-100 dark:bg-gray-800 p-6 rounded-lg">
    Content automatically adapts
  </div>
</div>
```

```css
/* Manual dark mode toggle with class selector */
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));
```

```html
<!-- Manual dark mode -->
<html class="dark">
  <body>
    <div class="bg-white dark:bg-black">
      Controlled by .dark class
    </div>
  </body>
</html>
```

```javascript
// Dark mode toggle logic
// On page load or theme change
document.documentElement.classList.toggle(
  "dark",
  localStorage.theme === "dark" ||
    (!("theme" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches)
);

// User chooses light mode
localStorage.theme = "light";

// User chooses dark mode
localStorage.theme = "dark";

// User chooses system preference
localStorage.removeItem("theme");
```

## State Variants

Styling elements based on pseudo-classes and parent/sibling state.

```html
<!-- Form state variants -->
<input
  type="email"
  required
  class="border-gray-300
         focus:border-sky-500
         focus:ring-2
         focus:ring-sky-300
         invalid:border-pink-500
         invalid:text-pink-600
         disabled:bg-gray-100
         disabled:opacity-50
         placeholder:text-gray-400"
  placeholder="you@example.com"
/>

<!-- List item variants -->
<ul role="list">
  <li class="py-4 first:pt-0 last:pb-0 odd:bg-gray-50 even:bg-white">
    Item content
  </li>
</ul>

<!-- Parent state with group -->
<a href="#" class="group">
  <h3 class="text-gray-900 group-hover:text-white">Title</h3>
  <p class="text-gray-500 group-hover:text-white">Description</p>
</a>

<!-- Sibling state with peer -->
<form>
  <input type="email" class="peer" />
  <p class="invisible peer-invalid:visible text-red-500">
    Please provide a valid email address.
  </p>
</form>

<!-- Has variant -->
<label class="has-checked:bg-indigo-50 has-checked:ring-indigo-200">
  <input type="radio" class="checked:border-indigo-500" />
  Option
</label>
```

## Responsive Design

Building mobile-first responsive layouts with breakpoint variants.

```html
<!-- Mobile-first responsive grid -->
<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
  <!-- Adapts from 1 to 6 columns -->
</div>

<!-- Responsive spacing and typography -->
<div class="px-4 sm:px-6 lg:px-8">
  <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold">
    Responsive heading
  </h1>
  <p class="mt-2 sm:mt-4 text-sm sm:text-base lg:text-lg">
    Text scales with viewport
  </p>
</div>

<!-- Container queries -->
<div class="@container">
  <div class="flex flex-col @md:flex-row @lg:gap-8">
    <!-- Responds to parent container width -->
  </div>
</div>

<!-- Min/max width breakpoints -->
<div class="hidden md:block">Desktop only</div>
<div class="block md:hidden">Mobile only</div>
<div class="min-[900px]:grid-cols-3">Custom breakpoint</div>
<div class="max-md:text-center">Below medium</div>
```

## Custom Utilities

Creating reusable custom utility classes with variant support.

```css
/* Simple custom utility */
@utility content-auto {
  content-visibility: auto;
}

/* Complex utility with nesting */
@utility scrollbar-hidden {
  &::-webkit-scrollbar {
    display: none;
  }
}

/* Functional utility with theme values */
@theme {
  --tab-size-2: 2;
  --tab-size-4: 4;
  --tab-size-github: 8;
}

@utility tab-* {
  tab-size: --value(--tab-size-*);
}

/* Supporting arbitrary, bare, and theme values */
@utility opacity-* {
  opacity: --value([percentage]);
  opacity: calc(--value(integer) * 1%);
  opacity: --value(--opacity-*);
}

/* Utility with modifiers */
@utility text-* {
  font-size: --value(--text-*, [length]);
  line-height: --modifier(--leading-*, [length], [*]);
}

/* Negative value support */
@utility inset-* {
  inset: --spacing(--value(integer));
  inset: --value([percentage], [length]);
}

@utility -inset-* {
  inset: --spacing(--value(integer) * -1);
  inset: calc(--value([percentage], [length]) * -1);
}
```

```html
<!-- Using custom utilities -->
<div class="content-auto scrollbar-hidden tab-4">
  Custom utilities work with variants
</div>

<div class="hover:tab-github lg:tab-[12]">
  Variants and arbitrary values supported
</div>

<div class="text-2xl/relaxed">
  Utility with modifier (font-size/line-height)
</div>
```

## Custom Variants

Registering custom conditional styles with the `@custom-variant` directive.

```css
/* Simple custom variant */
@custom-variant theme-midnight (&:where([data-theme="midnight"] *));

/* Variant with media query */
@custom-variant any-hover {
  @media (any-hover: hover) {
    &:hover {
      @slot;
    }
  }
}

/* ARIA state variant */
@custom-variant aria-asc (&[aria-sort="ascending"]);
@custom-variant aria-desc (&[aria-sort="descending"]);

/* Data attribute variant */
@custom-variant data-checked (&[data-ui~="checked"]);
```

```html
<!-- Using custom variants -->
<html data-theme="midnight">
  <button class="theme-midnight:bg-black theme-midnight:text-white">
    Midnight theme button
  </button>
</html>

<th aria-sort="ascending" class="aria-asc:rotate-0 aria-desc:rotate-180">
  Sortable column
</th>

<div data-ui="checked active" class="data-checked:underline">
  Checked state
</div>

<!-- Arbitrary variants -->
<div class="[&.is-dragging]:cursor-grabbing [&_p]:mt-4">
  One-off custom selectors
</div>
```

## Applying Variants in CSS

Using the `@variant` directive to apply variants within custom CSS.

```css
/* Single variant */
.my-element {
  background: white;

  @variant dark {
    background: black;
  }
}

/* Nested variants */
.my-button {
  background: white;

  @variant dark {
    background: gray;

    @variant hover {
      background: black;
    }
  }
}

/* Compiled output */
.my-element {
  background: white;
}

@media (prefers-color-scheme: dark) {
  .my-element {
    background: black;
  }
}
```

## Layer Organization

Organizing custom styles into Tailwind's cascade layers.

```css
@import "tailwindcss";

/* Base styles for HTML elements */
@layer base {
  h1 {
    font-size: var(--text-2xl);
    font-weight: bold;
  }

  h2 {
    font-size: var(--text-xl);
    font-weight: 600;
  }

  body {
    font-family: var(--font-body);
  }
}

/* Reusable component classes */
@layer components {
  .btn {
    padding: --spacing(2) --spacing(4);
    border-radius: var(--radius);
    font-weight: 600;
    transition: all 150ms;
  }

  .btn-primary {
    background-color: var(--color-blue-500);
    color: white;
  }

  .card {
    background-color: var(--color-white);
    border-radius: var(--radius-lg);
    padding: --spacing(6);
    box-shadow: var(--shadow-xl);
  }

  /* Third-party component overrides */
  .select2-dropdown {
    border-radius: var(--radius);
    box-shadow: var(--shadow-lg);
  }
}
```

```html
<!-- Components can be overridden by utilities -->
<div class="card rounded-none">
  Square corners despite card class
</div>

<button class="btn btn-primary hover:bg-blue-600 disabled:opacity-50">
  Component with utility overrides
</button>
```

## Functions and Directives

Using Tailwind's CSS functions for dynamic values and opacity adjustments.

```css
/* Alpha function for opacity */
.my-element {
  color: --alpha(var(--color-lime-300) / 50%);
  background: --alpha(var(--color-blue-500) / 25%);
}

/* Spacing function */
.my-element {
  margin: --spacing(4);
  padding: calc(--spacing(6) - 1px);
}

/* In arbitrary values */
<div class="py-[calc(--spacing(4)-1px)] mt-[--spacing(8)]">
  <!-- ... -->
</div>

/* Source directive for additional content */
@source "../node_modules/@my-company/ui-lib";

/* Apply directive for inline utilities */
.select2-dropdown {
  @apply rounded-b-lg shadow-md;
}

.select2-search {
  @apply rounded border border-gray-300;
}

.select2-results__group {
  @apply text-lg font-bold text-gray-900;
}
```

## Pseudo-elements

Styling ::before, ::after, ::placeholder, and other pseudo-elements.

```html
<!-- Required field indicator -->
<label>
  <span class="after:ml-0.5 after:text-red-500 after:content-['*']">
    Email
  </span>
  <input type="email" class="placeholder:text-gray-400 placeholder:italic" placeholder="you@example.com" />
</label>

<!-- File input styling -->
<input
  type="file"
  class="file:mr-4 file:rounded-full file:border-0 file:bg-violet-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-violet-700 hover:file:bg-violet-100"
/>

<!-- Custom list markers -->
<ul class="list-disc marker:text-sky-400">
  <li>First item</li>
  <li>Second item</li>
</ul>

<!-- Text selection styling -->
<div class="selection:bg-fuchsia-300 selection:text-fuchsia-900">
  <p>Select this text to see custom colors</p>
</div>

<!-- First letter drop cap -->
<p class="first-letter:float-left first-letter:mr-3 first-letter:text-7xl first-letter:font-bold first-line:uppercase first-line:tracking-widest">
  Typography with pseudo-elements
</p>
```

## Media Queries

Conditional styling based on user preferences and device capabilities.

```html
<!-- Reduced motion -->
<button class="transition hover:-translate-y-1 motion-reduce:transition-none motion-reduce:hover:translate-y-0">
  Respects user preference
</button>

<button class="motion-safe:animate-spin">
  Only animates if motion allowed
</button>

<!-- Contrast preference -->
<label>
  <input class="contrast-more:border-gray-400 contrast-less:border-gray-100" />
  <p class="opacity-75 contrast-more:opacity-100">
    Adjusts for contrast needs
  </p>
</label>

<!-- Pointer type -->
<div class="grid grid-cols-4 gap-2 pointer-coarse:grid-cols-2 pointer-coarse:gap-4">
  <!-- Larger touch targets on touch devices -->
</div>

<!-- Orientation -->
<div class="portrait:hidden">
  Hidden in portrait mode
</div>

<div class="landscape:grid-cols-2">
  Layout adapts to orientation
</div>

<!-- Print styles -->
<article class="print:hidden">
  Not shown when printing
</article>

<div class="hidden print:block">
  Only visible in print
</div>

<!-- Feature support -->
<div class="flex supports-[display:grid]:grid supports-backdrop-filter:backdrop-blur">
  Progressive enhancement
</div>
```

## Summary

Tailwind CSS provides a complete utility-first design system that eliminates the need for writing custom CSS in most cases. The framework's primary use cases include rapid prototyping, building production applications with consistent design systems, creating responsive layouts, implementing dark mode, and maintaining design consistency across large teams. By using utility classes directly in markup, developers can iterate quickly, avoid naming conventions, and prevent CSS bloat since only used styles are generated.

The v4.1 release enhances the developer experience with CSS-first configuration, eliminating JavaScript configuration files for most projects. Integration patterns include using the Vite plugin for modern frameworks, PostCSS for custom build pipelines, the Tailwind CLI for simple projects, and CDN scripts for rapid prototyping. The framework excels at component-driven development when combined with React, Vue, Svelte, or other modern frameworks, where utility classes are co-located with component logic. Custom design systems can be fully defined in CSS using `@theme`, with project-specific utilities and variants extending the framework's capabilities without writing JavaScript plugins.

# React.dev Documentation Site

React.dev is the official documentation website for the React JavaScript library, built with Next.js 15.1. The site provides comprehensive learning resources, API references, community pages, and a blog, all rendered from Markdown/MDX content files. It features an interactive code playground powered by Sandpack, advanced MDX processing with custom components, and a sophisticated build system that compiles markdown into optimized React components at build time.

The architecture leverages Next.js static site generation to pre-render all markdown pages, using a custom MDX compilation pipeline that transforms markdown files into serialized React trees cached on disk. The site supports multiple sections (Learn, Reference, Community, Blog) with distinct navigation structures, includes Algolia-powered search, RSS feed generation, error decoder pages, and implements hot-reloading for markdown content during development. Built with TypeScript, Tailwind CSS, and React 19, it demonstrates modern web documentation practices with accessibility, responsive design, and developer experience as priorities.

## Site Configuration

Site-wide configuration settings

```javascript
// src/siteConfig.js
const { siteConfig } = require('./src/siteConfig');

// Configuration object
const config = {
  version: '19.2',
  languageCode: 'en',
  hasLegacySite: true,
  isRTL: false,
  copyright: `Copyright © ${new Date().getFullYear()} Facebook Inc. All Rights Reserved.`,
  repoUrl: 'https://github.com/facebook/react',
  twitterUrl: 'https://twitter.com/reactjs',
  algolia: {
    appId: '1FCF9AYYAT',
    apiKey: '1b7ad4e1c89e645e351e59d40544eda1',
    indexName: 'beta-react'
  }
};

// Usage in components
import { siteConfig } from '../siteConfig';
console.log(siteConfig.version); // "19.2"
```

## MDX Content Processing

Compile markdown files to React components

```typescript
// src/utils/compileMDX.ts
import compileMDX from 'utils/compileMDX';

// Compile MDX file to serialized React tree
const mdxContent = `
---
title: Getting Started with React
description: Learn React basics
---

# Hello React

This is **bold** text.

<Note>
This is a custom MDX component
</Note>
`;

const result = await compileMDX(mdxContent, 'learn/getting-started', {});

// Returns
const output = {
  content: '["$r","wrapper",null,{"children":[...]}]', // Serialized React tree
  toc: '[{"url":"#hello-react","depth":1,"text":"Hello React"}]', // Table of contents
  meta: {
    title: 'Getting Started with React',
    description: 'Learn React basics'
  },
  languages: null
};

// Cached to node_modules/.cache/react-docs-mdx/ for fast rebuilds
```

## Dynamic Page Routing

Next.js catch-all route for markdown pages

```javascript
// src/pages/[[...markdownPath]].js
import { Page } from 'components/Layout/Page';

// This file handles all routes like /learn/foo, /reference/bar, etc.
export async function getStaticProps(context) {
  const path = (context.params.markdownPath || []).join('/') || 'index';

  // Read markdown file
  const mdx = fs.readFileSync(`src/content/${path}.md`, 'utf8');

  // Compile MDX to JSON
  const { toc, content, meta, languages } = await compileMDX(mdx, path, {});

  return {
    props: { toc, content, meta, languages }
  };
}

export async function getStaticPaths() {
  // Find all .md files recursively in src/content/
  const files = await getFiles('src/content');

  return {
    paths: files.map(file => ({
      params: { markdownPath: getSegments(file) }
    })),
    fallback: false // All pages pre-rendered at build time
  };
}

export default function Layout({ content, toc, meta, languages }) {
  const parsedContent = JSON.parse(content, reviveNodeOnClient);
  const parsedToc = JSON.parse(toc, reviveNodeOnClient);

  return (
    <Page toc={parsedToc} meta={meta} languages={languages}>
      {parsedContent}
    </Page>
  );
}
```

## Custom MDX Components

Rich interactive components available in markdown

```typescript
// src/components/MDX/MDXComponents.tsx
import { MDXComponents } from 'components/MDX/MDXComponents';

// Example MDX file: src/content/learn/state-management.md
`
# State Management

<Intro>
Learn how to manage state in React applications.
</Intro>

<YouWillLearn>
- How to use useState
- When to lift state up
- How to share state between components
</YouWillLearn>

<Sandpack>

\`\`\`js App.js
import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
\`\`\`

</Sandpack>

<Pitfall>
Don't mutate state directly. Always use setState.
</Pitfall>

<DeepDive title="How does React track changes?" excerpt="Learn about React's reconciliation">

React uses a virtual DOM to efficiently update the UI...

</DeepDive>

<Note>
This is an important note for developers.
</Note>

<Challenges>

#### Challenge 1: Add a reset button

Add a button that resets the counter to 0.

<Hint>
You'll need to call setCount(0).
</Hint>

<Solution>

\`\`\`js
function Counter() {
  const [count, setCount] = useState(0);
  return (
    <>
      <button onClick={() => setCount(count + 1)}>Count: {count}</button>
      <button onClick={() => setCount(0)}>Reset</button>
    </>
  );
}
\`\`\`

</Solution>

</Challenges>
`

// All components automatically available in MDX:
// Intro, YouWillLearn, Sandpack, Pitfall, DeepDive, Note,
// Challenges, Hint, Solution, Diagram, CodeDiagram, etc.
```

## Sandpack Integration

Interactive code playground in documentation

```typescript
// src/components/MDX/Sandpack/SandpackRoot.tsx
import { SandpackProvider } from '@codesandbox/sandpack-react/unstyled';

// Usage in MDX files
`
<Sandpack>

\`\`\`js App.js
import { useState } from 'react';

export default function App() {
  const [name, setName] = useState('React');

  return (
    <div>
      <input value={name} onChange={e => setName(e.target.value)} />
      <h1>Hello {name}!</h1>
    </div>
  );
}
\`\`\`

\`\`\`css styles.css
h1 {
  color: blue;
  font-family: sans-serif;
}
\`\`\`

</Sandpack>
`

// Multi-file examples automatically detected
// Creates live-editable code sandbox with hot reload
// Supports React, CSS, and multiple JS files
```

## Page Layout System

Main layout component with navigation

```typescript
// src/components/Layout/Page.tsx
import { Page } from 'components/Layout/Page';

// Automatic section detection and routing
function MyDocPage() {
  return (
    <Page
      toc={[
        { url: '#intro', depth: 1, text: 'Introduction' },
        { url: '#usage', depth: 2, text: 'Usage' }
      ]}
      routeTree={sidebarLearn}
      meta={{
        title: 'Getting Started',
        description: 'Learn React basics',
        version: 'canary' // Optional: shows "Canary only" badge
      }}
      section="learn"
      languages={null}
    >
      <h1 id="intro">Introduction</h1>
      <p>Content here...</p>
      <h2 id="usage">Usage</h2>
      <p>More content...</p>
    </Page>
  );
}

// Renders with:
// - Top navigation with search
// - Sidebar navigation (for learn/reference/community)
// - Table of contents (right sidebar on desktop)
// - Breadcrumbs
// - Previous/Next page navigation
// - Footer
```

## RSS Feed Generation

Generate blog RSS feed

```javascript
// src/utils/rss.js - scripts/generateRss.js
const { generateRssFeed } = require('./src/utils/rss');

// Called during build in getStaticProps
generateRssFeed();

// Reads all blog posts from src/content/blog/
// Extracts frontmatter (title, author, date, description)
// Generates public/rss.xml

// Blog post frontmatter requirements:
`
---
title: "React 19 Released"
author: "React Team"
date: "2024-04-25"
description: "We're excited to announce React 19"
---

Blog content here...
`

// Output: https://react.dev/rss.xml
// Subscribed by feed readers for React blog updates
```

## Markdown to HTML Plugin System

Remark plugins for markdown processing

```javascript
// plugins/markdownToHtml.js
const remark = require('remark');
const { remarkPlugins, markdownToHtml } = require('../plugins/markdownToHtml');

// Convert markdown to HTML (used for RSS feed descriptions)
const markdown = `
# Hello World

This is a [link](https://react.dev) to the docs.

![React Logo](/logo.png "React")
`;

const html = await markdownToHtml(markdown);

// Returns processed HTML with:
// - External links get target="_blank" and rel="noopener"
// - Custom header IDs for i18n (#hello-world)
// - Improved image syntax
// - Unwrapped images (no <p> wrapper)
// - Smart quotes and typography (curly quotes, em dashes)

console.log(html);
// Output:
// <h1 id="hello-world">Hello World</h1>
// <p>This is a <a href="https://react.dev" target="_blank" rel="noopener">link</a>...</p>
// <img src="/logo.png" alt="React Logo" title="React" />
```

## Next.js Configuration

Build configuration with webpack customization

```javascript
// next.config.js
const nextConfig = {
  pageExtensions: ['jsx', 'js', 'ts', 'tsx', 'mdx', 'md'],
  reactStrictMode: true,
  experimental: {
    scrollRestoration: true,
    reactCompiler: true // Uses React Compiler for optimization
  },
  webpack: (config, { dev, isServer, ...options }) => {
    // Bundle analyzer for production builds
    if (process.env.ANALYZE) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: options.isServer
            ? '../analyze/server.html'
            : './analyze/client.html'
        })
      );
    }

    // Custom module replacements for browser compatibility
    const { NormalModuleReplacementPlugin, IgnorePlugin } = require('webpack');
    config.resolve.alias['use-sync-external-store/shim'] = 'react';

    // ESLint depends on the CommonJS version of esquery,
    // but Webpack loads the ESM version by default. This
    // alias ensures the correct version is used.
    config.resolve.alias['esquery'] = 'esquery/dist/esquery.min.js';

    // Replace modules for client-side compatibility
    config.plugins.push(
      new NormalModuleReplacementPlugin(/^raf$/, require.resolve('./src/utils/rafShim.js')),
      new NormalModuleReplacementPlugin(/^process$/, require.resolve('./src/utils/processShim.js')),
      new IgnorePlugin({
        checkResource(resource, context) {
          // Skip ESLint built-in rules to reduce bundle size
          return /\/eslint\/lib\/rules$/.test(context) && /\.\/[\w-]+(\.js)?$/.test(resource);
        }
      })
    );

    return config;
  }
};

// Run with: npm run analyze
// Generates bundle size visualization
```

## Development Workflow

Local development and content editing

```bash
# Install dependencies
yarn install

# Start development server with hot reload for markdown
yarn dev
# Opens http://localhost:3000
# Changes to src/content/*.md hot-reload automatically
# Changes to src/components/*.tsx hot-reload automatically

# Type checking
yarn tsc

# Linting and formatting
yarn lint
yarn prettier

# Fix heading IDs in markdown
yarn fix-headings

# Check all (CI validation)
yarn ci-check
# Runs: prettier, lint, tsc, lint-heading-ids, rss, deadlinks

# Build for production
yarn build
# Compiles all MDX, generates static HTML, optimizes assets, downloads fonts
# Output: .next/ directory

# Start production server
yarn start

# Generate RSS feed
yarn rss
```

## Content Structure

Organizing documentation content

```bash
src/content/
├── learn/              # Step-by-step tutorials
│   ├── index.md        # /learn landing page
│   ├── installation.md # /learn/installation
│   ├── describing-the-ui.md
│   ├── adding-interactivity.md
│   └── managing-state.md
├── reference/          # API documentation
│   ├── react/
│   │   ├── index.md    # /reference/react
│   │   ├── useState.md
│   │   └── useEffect.md
│   └── react-dom/
├── community/          # Community resources
│   ├── team.md
│   ├── conferences.md
│   └── meetups.md
├── blog/               # React blog posts
│   └── 2024/04/25/
│       └── react-19-upgrade-guide.md
├── warnings/           # Warning/error explanations
│   └── invalid-hook-call-warning.md
└── errors/             # Error code explanations
    └── *.md            # Error decoder content

# Frontmatter example:
---
title: useState
description: Add state to your components
---

# Content routing:
# src/content/learn/installation.md → https://react.dev/learn/installation
# src/content/reference/react/useState.md → https://react.dev/reference/react/useState
# src/content/errors/*.md → https://react.dev/errors/[errorCode]
```

## Error Decoder Pages

Dynamic error explanation pages

```typescript
// src/pages/errors/[errorCode].tsx
// Handles routes like /errors/418, /errors/423, etc.

// URL structure:
// https://react.dev/errors/418 → Renders error code 418 explanation
// https://react.dev/errors/423 → Renders error code 423 explanation

// Error markdown files stored in:
// src/content/errors/418.md
// src/content/errors/423.md

// Separate from main catch-all route
// Excluded from getStaticPaths in [[...markdownPath]].js (line 157)
// Uses dedicated error page component with ErrorDecoder context
```

## Sidebar Navigation

Dynamic navigation structure

```json
// src/sidebarLearn.json
{
  "title": "Learn React",
  "path": "/learn",
  "routes": [
    {
      "title": "Get Started",
      "path": "/learn",
      "routes": [
        {
          "title": "Quick Start",
          "path": "/learn",
          "description": "Learn React basics"
        },
        {
          "title": "Installation",
          "path": "/learn/installation",
          "description": "Set up your environment"
        }
      ]
    },
    {
      "title": "Describing the UI",
      "path": "/learn/describing-the-ui",
      "tags": ["components", "jsx"],
      "routes": [
        {
          "title": "Your First Component",
          "path": "/learn/your-first-component"
        }
      ]
    }
  ]
}

// Used by Page component for sidebar rendering
// Supports nested routes, descriptions, and tags
// Separate files: sidebarLearn, sidebarReference, sidebarCommunity, sidebarBlog
```

React.dev serves as both a learning platform and API reference for React developers. The main use cases include: (1) Progressive learning through the "Learn React" section, which guides developers from basics to advanced concepts with interactive examples; (2) API reference documentation providing exhaustive details on React hooks, components, and APIs; (3) Community resources including team information, conferences, and translations; (4) Blog posts announcing new features, releases, and best practices. The site architecture prioritizes performance through static generation, developer experience through hot reload, and content quality through strict linting and validation.

Integration patterns demonstrate modern documentation site architecture: MDX compilation happens at build time with aggressive caching for fast rebuilds; Sandpack provides in-browser code execution without external dependencies; the sidebar/navigation system adapts to different sections automatically; custom MDX components (Pitfall, Note, DeepDive, Challenges) create consistent, accessible UI patterns; Algolia search indexes all content for fast discovery; RSS feeds enable content syndication; and the entire codebase uses TypeScript for type safety. The system is designed to be translated (with language detection and routing), accessible (semantic HTML, ARIA labels), and maintainable (clear separation between content and presentation).
