export const surface = {
  /**
   * Base glass surface used for cards and panels.
   */
  base: "glass-layer rounded-3xl border border-white/10 shadow-[var(--shadow-soft)]",
  /**
   * Stronger glass surface for elevated content (modals, flyouts).
   */
  strong: "glass-layer-strong rounded-3xl border border-white/10 shadow-[var(--shadow-strong)]",
  /**
   * Interactive surface with subtle gradient border response.
   */
  interactive:
    "glass-layer glass-border hover:shadow-[var(--shadow-glow)] focus-visible:shadow-[var(--shadow-glow)] rounded-[1.4rem] transition-all duration-300 ease-out",
};

export const transitions = {
  base: "transition-all duration-300 ease-out",
  soft: "transition-all duration-200 ease-out",
  slow: "transition-all duration-500 ease-out",
};

export const layout = {
  container: "mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8",
  section: "py-12 sm:py-16 lg:py-20",
  sectionTight: "py-8 sm:py-12 lg:py-16",
};

export const typography = {
  headline:
    "text-balance text-3xl font-semibold tracking-tight sm:text-4xl lg:text-5xl gradient-text leading-tight",
  subheading: "text-lg sm:text-xl text-muted-foreground max-w-2xl text-balance",
  body: "text-base leading-relaxed text-muted-foreground",
};

export const themeTokens = {
  glass: {
    blur: 16,
    radius: 18,
    opacity: 0.16,
  },
  hover: {
    float: "hover:-translate-y-1 hover:scale-[1.01]",
    glow: "hover:shadow-[var(--shadow-glow)]",
  },
};
