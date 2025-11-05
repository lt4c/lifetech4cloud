import type {
  AnnouncementDetail,
  AnnouncementSummary,
  BannerMessage,
  KyaroPrompt,
  SupportAttachment,
  SupportMessage,
  SupportThread,
  UserProfile,
  VersionInfo,
  VpsProduct,
  VpsSession,
} from "./types";

const rawUseMocks = (import.meta.env.VITE_USE_MOCKS ?? "true").toString().toLowerCase();
const USE_MOCKS = rawUseMocks === "true";

const nowIso = () => new Date().toISOString();

const createJsonResponse = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const createTextResponse = (text: string, status = 200): Response =>
  new Response(text, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });

const parseBody = (body?: BodyInit | null): Record<string, unknown> => {
  if (!body || typeof body !== "string") {
    return {};
  }
  try {
    return JSON.parse(body) as Record<string, unknown>;
  } catch {
    return {};
  }
};

const toSummary = (detail: AnnouncementDetail): AnnouncementSummary => ({
  id: detail.id,
  slug: detail.slug,
  title: detail.title,
  excerpt: detail.excerpt,
  hero_image_url: detail.hero_image_url,
  created_at: detail.created_at,
  updated_at: detail.updated_at,
});

type MockState = {
  profile: UserProfile;
  banner: BannerMessage;
  version: VersionInfo;
  kyaro: KyaroPrompt;
  products: VpsProduct[];
  sessions: VpsSession[];
  threads: SupportThread[];
  announcements: AnnouncementDetail[];
};

const mockState: MockState = {
  profile: {
    id: "mock-user",
    email: "mock.user@example.com",
    username: "mockuser",
    display_name: "Mock Operator",
    avatar_url: null,
    phone_number: null,
    coins: 4200,
    roles: ["member"],
    is_admin: false,
    has_admin: false,
  },
  banner: {
    message:
      "🚀 Welcome to the LT4C mock environment.\nThis build renders entirely offline with liquid glass surfaces.",
    updated_at: nowIso(),
  },
  version: {
    channel: "dev",
    version: "0.0.0-mock",
    description: "Mock build for offline testing.",
    updated_at: nowIso(),
    updated_by: "mock-bot",
  },
  kyaro: {
    prompt:
      "You are Kyaro, a friendly assistant guiding users through the LifeTech4Cloud interface in mock mode.",
    version: 1,
    updated_at: nowIso(),
    updated_by: "mock-bot",
  },
  products: [
    {
      id: "mock-studio",
      name: "Studio Glass",
      description: "4 vCPU • 8 GB RAM • Perfect for creative suites.",
      price_coins: 2400,
      created_at: nowIso(),
      updated_at: nowIso(),
    },
    {
      id: "mock-pro",
      name: "Velocity Pro",
      description: "8 vCPU • 16 GB RAM • Tuned for motion graphics.",
      price_coins: 6400,
      created_at: nowIso(),
      updated_at: nowIso(),
    },
  ],
  sessions: [
    {
      id: "sess-1",
      status: "ready",
      checklist: [],
      created_at: nowIso(),
      updated_at: nowIso(),
      expires_at: null,
      product: { id: "mock-studio", name: "Studio Glass", description: "Mock session" },
      worker_id: null,
      stream: undefined,
      rdp: undefined,
      has_log: false,
      worker_route: null,
      log_url: null,
      provision_action: null,
      worker_action: null,
    },
  ],
  threads: [
    {
      id: "thread-1",
      source: "ai",
      status: "open",
      created_at: nowIso(),
      updated_at: nowIso(),
      user_id: "mock-user",
      messages: [
        {
          id: "msg-1",
          sender: "ai",
          role: "assistant",
          content:
            "👋 Hi! This is the mock support assistant. Ask anything and I will respond instantly.",
          attachments: [],
          meta: null,
          created_at: nowIso(),
        },
      ],
    },
  ],
  announcements: [
    {
      id: "ann-1",
      slug: "mock-release",
      title: "Mock release notes",
      excerpt: "Liquid glass shells are now available offline.",
      hero_image_url: null,
      created_at: nowIso(),
      updated_at: nowIso(),
      content:
        "## Mock release\n\n- ✨ Glass surfaces shimmer without network calls.\n- ⚡ Magnetic buttons react instantly.\n- 🌓 Dark mode is now the default experience.",
      attachments: [],
      created_by: "mock-team",
    },
  ],
};

const findAnnouncement = (identifier: string): AnnouncementDetail | undefined =>
  mockState.announcements.find(
    (announcement) => announcement.id === identifier || announcement.slug === identifier,
  );

const handleJsonRequest = (path: string, method: string, body: Record<string, unknown>) => {
  switch (true) {
    case path === "/me" && method === "GET":
      return createJsonResponse(mockState.profile);
    case path === "/me" && method === "PATCH": {
      mockState.profile = {
        ...mockState.profile,
        display_name:
          typeof body.display_name === "string"
            ? (body.display_name as string)
            : mockState.profile.display_name,
        phone_number:
          typeof body.phone_number === "string"
            ? (body.phone_number as string)
            : mockState.profile.phone_number,
      };
      return createJsonResponse(mockState.profile);
    }
    case path === "/logout" && method === "POST":
      return createJsonResponse({ ok: true });
    case path === "/banner" && method === "GET":
    case path === "/api/v1/admin/settings/banner":
      return createJsonResponse(mockState.banner);
    case (path === "/version" || path === "/api/v1/admin/settings/version") && method === "GET":
      return createJsonResponse(mockState.version);
    case path === "/api/v1/admin/status/health" && method === "GET":
      return createJsonResponse({
        api_up: true,
        version: mockState.version.version,
        build_time: mockState.version.updated_at,
      });
    case path === "/api/v1/admin/kyaro/prompt" && method === "GET":
      return createJsonResponse(mockState.kyaro);
    case path === "/wallet" && method === "GET":
      return createJsonResponse({ balance: mockState.profile.coins });
    case path === "/vps/products" && method === "GET":
      return createJsonResponse(mockState.products);
    case path === "/vps/sessions" && method === "GET":
      return createJsonResponse({ sessions: mockState.sessions });
    case path === "/support/threads" && method === "GET":
      return createJsonResponse({ threads: mockState.threads });
    case path === "/support/threads" && method === "POST": {
      const message =
        typeof body.message === "string" ? (body.message as string) : "New mock thread";
      const attachments = Array.isArray(body.attachments)
        ? (body.attachments as SupportAttachment[])
        : [];
      const newThread: SupportThread = {
        id: `thread-${Date.now()}`,
        source: "human",
        status: "open",
        created_at: nowIso(),
        updated_at: nowIso(),
        user_id: mockState.profile.id,
        messages: [
          {
            id: `msg-${Date.now()}`,
            sender: "user",
            role: "user",
            content: message,
            attachments,
            meta: null,
            created_at: nowIso(),
          },
        ],
      };
      mockState.threads = [newThread, ...mockState.threads];
      return createJsonResponse(newThread);
    }
    case path.startsWith("/support/threads/") && method === "GET": {
      const [, , , threadId] = path.split("/");
      const thread = mockState.threads.find((item) => item.id === threadId);
      return createJsonResponse(thread ?? mockState.threads[0]);
    }
    case path.endsWith("/message") && method === "POST": {
      const threadId = path.split("/")[3];
      const thread =
        mockState.threads.find((item) => item.id === threadId) ?? mockState.threads[0];
      const message: SupportMessage = {
        id: `msg-${Date.now()}`,
        sender: "user",
        role: "user",
        content:
          typeof body.message === "string"
            ? (body.message as string)
            : "Message sent in mock mode.",
        attachments: Array.isArray(body.attachments)
          ? (body.attachments as SupportAttachment[])
          : [],
        meta: null,
        created_at: nowIso(),
      };
      thread.messages = [...thread.messages, message];
      thread.updated_at = nowIso();
      return createJsonResponse(thread);
    }
    case path === "/support/ask" && method === "POST": {
      const threadId =
        typeof body.thread_id === "string" ? (body.thread_id as string) : undefined;
      const thread =
        mockState.threads.find((item) => item.id === threadId) ?? mockState.threads[0];
      const reply: SupportMessage = {
        id: `msg-${Date.now()}`,
        sender: "ai",
        role: "assistant",
        content:
          "🤖 Kyaro (mock): I’m running entirely offline. Try the new liquid glass components!",
        attachments: [],
        meta: null,
        created_at: nowIso(),
      };
      thread.messages = [...thread.messages, reply];
      thread.updated_at = nowIso();
      return createJsonResponse(thread);
    }
    case path === "/announcements" && method === "GET":
      return createJsonResponse(mockState.announcements.map(toSummary));
    case path.startsWith("/announcements/slug/") && method === "GET": {
      const slug = path.replace("/announcements/slug/", "");
      const detail = findAnnouncement(slug) ?? mockState.announcements[0];
      return createJsonResponse(detail);
    }
    case path.startsWith("/announcements/") && method === "GET": {
      const id = path.replace("/announcements/", "");
      const detail = findAnnouncement(id) ?? mockState.announcements[0];
      return createJsonResponse(detail);
    }
    default:
      if (method === "GET") {
        return createJsonResponse({});
      }
      return createJsonResponse({ ok: true });
  }
};

const handleTextRequest = (path: string): Response => {
  if (path === "/metrics") {
    return createTextResponse(
      [
        '# HELP rewarded_ads_prepare_total Total prepare calls.',
        '# TYPE rewarded_ads_prepare_total counter',
        'rewarded_ads_prepare_total{status="ok"} 10',
        'rewarded_ads_prepare_total{status="rejected"} 2',
        '# HELP rewarded_ads_reward_amount_total Total reward coins.',
        '# TYPE rewarded_ads_reward_amount_total counter',
        "rewarded_ads_reward_amount_total 4200",
        '# HELP rewarded_ads_failure_ratio Failure ratio.',
        '# TYPE rewarded_ads_failure_ratio gauge',
        "rewarded_ads_failure_ratio 0.05",
      ].join("\n"),
    );
  }
  return createTextResponse("", 200);
};

const resolveMockResponse = (url: URL, init?: RequestInit): Response | undefined => {
  const method = (init?.method ?? "GET").toString().toUpperCase();
  const path = url.pathname;

  if (path === "/metrics") {
    return handleTextRequest(path);
  }

  return handleJsonRequest(path, method, parseBody(init?.body));
};

export const setupMockFetch = () => {
  if (!USE_MOCKS || typeof window === "undefined" || typeof window.fetch !== "function") {
    return;
  }

  const originalFetch = window.fetch.bind(window);

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const resolvedUrl =
      typeof input === "string"
        ? new URL(input, window.location.origin)
        : input instanceof URL
        ? input
        : new URL(input.url);

    const mockResponse = resolveMockResponse(resolvedUrl, init);
    if (mockResponse) {
      return mockResponse;
    }

    return originalFetch(input, init);
  };
};

