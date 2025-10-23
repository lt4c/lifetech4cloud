import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, Loader2, Play, ShieldAlert } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/context/AuthContext";
import {
  ApiError,
  completeMonetagAd,
  fetchRewardMetrics,
  fetchRewardPolicy,
  fetchWalletBalance,
  prepareRewardedAd,
} from "@/lib/api-client";
import type {
  PrepareAdResponse,
  RewardMetricsSummary,
  RewardPolicy,
  RewardProviderConfig,
  WalletBalance,
} from "@/lib/types";

declare global {
  interface Window {
    turnstile?: {
      render?: (container: HTMLElement | string, options: Record<string, unknown>) => unknown;
      execute?: (
        siteKey: string,
        options?: { action?: string; cData?: string },
      ) => Promise<string>;
    };
    google?: any;
    monetag?: {
      display?: (zoneId: string, options?: Record<string, unknown>) => void;
      run?: (zoneId: string) => void;
    };
  }
}

const PLACEMENT = "earn";
const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY ?? "";
const CLIENT_SIGNING_KEY = import.meta.env.VITE_ADS_CLIENT_SIGNING_KEY ?? "";

let turnstileLoader: Promise<void> | null = null;
let imaLoader: Promise<void> | null = null;
const monetagLoaders = new Map<string, Promise<void>>();

const ensureTurnstile = async (): Promise<void> => {
  if (!TURNSTILE_SITE_KEY || typeof window === "undefined") {
    return;
  }
  if (window.turnstile) {
    return;
  }
  if (!turnstileLoader) {
    turnstileLoader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = `https://challenges.cloudflare.com/turnstile/v0/api.js?render=${TURNSTILE_SITE_KEY}`;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("KhÃ´ng thá»ƒ táº£i Cloudflare Turnstile"));
      document.head.appendChild(script);
    });
  }
  await turnstileLoader;
};

const ensureImaSdk = async (): Promise<void> => {
  if (typeof window === "undefined") {
    throw new Error("IMA SDK yÃªu cáº§u mÃ´i trÆ°á»ng trÃ¬nh duyá»‡t");
  }
  if (window.google?.ima) {
    return;
  }
  if (!imaLoader) {
    imaLoader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://imasdk.googleapis.com/js/sdkloader/ima3.js";
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("KhÃ´ng thá»ƒ táº£i Google IMA SDK"));
      document.head.appendChild(script);
    });
  }
  await imaLoader;
};

const ensureMonetagScript = async (scriptUrl: string): Promise<void> => {
  if (!scriptUrl) {
    throw new Error("Thiáº¿u script Monetag");
  }
  if (typeof document === "undefined") {
    throw new Error("Monetag yÃªu cáº§u mÃ´i trÆ°á»ng trÃ¬nh duyá»‡t");
  }
  if (document.querySelector(`script[data-monetag-src="${scriptUrl}"]`)) {
    return;
  }
  let loader = monetagLoaders.get(scriptUrl);
  if (!loader) {
    loader = new Promise<void>((resolve, reject) => {
      const script = document.createElement("script");
      script.src = scriptUrl;
      script.async = true;
      (script as HTMLScriptElement).dataset.monetagSrc = scriptUrl;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("KhÃ´ng thá»ƒ táº£i script Monetag"));
      document.head.appendChild(script);
    });
    monetagLoaders.set(scriptUrl, loader);
  }
  await loader;
};

const showMonetagAd = (zoneId: string, container: HTMLElement | null) => {
  if (!container) {
    throw new Error("KhÃ´ng tÃ¬m tháº¥y vÃ¹ng hiá»ƒn thá»‹ Monetag");
  }
  container.innerHTML = "";
  try {
    if (window.monetag?.display) {
      window.monetag.display(zoneId, { container });
      return;
    }
  } catch (error) {
    console.warn("Monetag display() failed", error);
  }
  try {
    if (window.monetag?.run) {
      window.monetag.run(zoneId);
      return;
    }
  } catch (error) {
    console.warn("Monetag run() failed", error);
  }
  const fallback = document.createElement("div");
  fallback.className = "monetag-zone";
  fallback.dataset.zone = zoneId;
  container.appendChild(fallback);
};

const executeTurnstile = async (): Promise<string | null> => {
  if (!TURNSTILE_SITE_KEY) {
    return null;
  }
  await ensureTurnstile();
  const turnstile = window.turnstile;
  if (!turnstile?.execute) {
    throw new Error("Cloudflare Turnstile chÆ°a sáºµn sÃ ng");
  }
  return turnstile.execute(TURNSTILE_SITE_KEY, { action: "ads_prepare" });
};

const signPrepareRequest = async (
  userId: string,
  clientNonce: string,
  timestamp: string,
  placement: string,
): Promise<string | null> => {
  if (!CLIENT_SIGNING_KEY || typeof window === "undefined" || !window.crypto?.subtle) {
    return null;
  }
  const encoder = new TextEncoder();
  const keyMaterial = encoder.encode(CLIENT_SIGNING_KEY);
  const cryptoKey = await window.crypto.subtle.importKey(
    "raw",
    keyMaterial,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const payload = encoder.encode(`${userId}|${clientNonce}|${timestamp}|${placement}`);
  const buffer = await window.crypto.subtle.sign("HMAC", cryptoKey, payload);
  return Array.from(new Uint8Array(buffer))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
};

const collectClientHints = (): Record<string, string> => {
  if (typeof navigator === "undefined") {
    return {};
  }
  const hints: Record<string, string> = { ua: navigator.userAgent };
  const uaData = (navigator as unknown as { userAgentData?: any }).userAgentData;
  if (uaData) {
    hints.platform = uaData.platform ?? "";
    hints.mobile = String(uaData.mobile ?? false);
    const brands =
      uaData.brands ?? uaData.getHighEntropyValues?.(["model", "platformVersion"]);
    if (Array.isArray(brands)) {
      hints.brands = brands
        .map(
          (item: { brand?: string; version?: string }) =>
            `${item.brand ?? ""}:${item.version ?? ""}`,
        )
        .join("|");
    }
  }
  try {
    hints.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone ?? "";
  } catch {
    /* ignore */
  }
  return hints;
};

const formatSeconds = (seconds: number): string => {
  if (!Number.isFinite(seconds)) {
    return "--";
  }
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
};
const providerDisplayName = (provider: string): string => {
  switch (provider) {
    case "monetag":
      return "Monetag";
    case "gma":
      return "Google Ads";
    default:
      return provider.toUpperCase();
  }
};

type EarnStatus =
  | "idle"
  | "preparing"
  | "loading"
  | "playing"
  | "verifying"
  | "success"
  | "error";

const initialMetrics: RewardMetricsSummary = {
  prepareOk: 0,
  prepareRejected: 0,
  ssvSuccess: 0,
  ssvInvalid: 0,
  ssvDuplicate: 0,
  ssvError: 0,
  rewardCoins: 0,
  failureRatio: 0,
  effectiveDailyCap: 0,
};

const Earn = () => {
  const { profile, refresh } = useAuth();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const adContainerRef = useRef<HTMLDivElement | null>(null);
  const monetagContainerRef = useRef<HTMLDivElement | null>(null);
  const [status, setStatus] = useState<EarnStatus>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(null);
  const [metricsSnapshot, setMetricsSnapshot] =
    useState<RewardMetricsSummary>(initialMetrics);
  const [selectedProvider, setSelectedProvider] = useState<string>("monetag");
  const [activeProvider, setActiveProvider] = useState<string>("monetag");
  const [monetagElapsed, setMonetagElapsed] = useState<number>(0);
  const [monetagPaused, setMonetagPaused] = useState<boolean>(false);
  const monetagTimerRef = useRef<number | null>(null);
  const monetagElapsedRef = useRef<number>(0);
  const monetagActiveRef = useRef<boolean>(false);
  const monetagCancelRef = useRef<((reason: Error) => void) | null>(null);
  const monetagCleanupRef = useRef<(() => void) | null>(null);

  const policyQuery = useQuery<RewardPolicy>({
    queryKey: ["ads-policy"],
    queryFn: fetchRewardPolicy,
    staleTime: 60_000,
  });
  const policy = policyQuery.data;
  const isLoadingPolicy = policyQuery.isLoading;
  const refetchPolicy = policyQuery.refetch;

  const walletQuery = useQuery<WalletBalance>({
    queryKey: ["wallet-balance"],
    queryFn: fetchWalletBalance,
    staleTime: 5_000,
    refetchOnWindowFocus: true,
    enabled: Boolean(profile),
  });
  const walletBalance = walletQuery.data?.balance ?? profile?.coins ?? 0;
  const refetchWallet = walletQuery.refetch;

  const metricsQuery = useQuery<RewardMetricsSummary>({
    queryKey: ["reward-metrics"],
    queryFn: fetchRewardMetrics,
    staleTime: 60_000,
  });
  const refetchMetrics = metricsQuery.refetch;

  const cooldownRemaining = useMemo(() => {
    if (!cooldownUntil) {
      return 0;
    }
    return Math.max(0, Math.ceil((cooldownUntil - Date.now()) / 1000));
  }, [cooldownUntil]);

  useEffect(() => {
    if (!cooldownUntil) {
      return;
    }
    const timer = window.setInterval(() => {
      if (Date.now() >= cooldownUntil) {
        setCooldownUntil(null);
        setStatus("idle");
        window.clearInterval(timer);
      }
    }, 1_000);
    return () => window.clearInterval(timer);
  }, [cooldownUntil]);

  useEffect(() => {
    if (metricsQuery.data) {
      setMetricsSnapshot(metricsQuery.data);
    }
  }, [metricsQuery.data]);

  const stopMonetagWatcher = useCallback(() => {
    monetagActiveRef.current = false;
    if (monetagCancelRef.current) {
      monetagCancelRef.current(new Error("Monetag watcher cancelled"));
      return;
    }
    if (monetagCleanupRef.current) {
      monetagCleanupRef.current();
      monetagCleanupRef.current = null;
    }
  }, []);

  const startMonetagWatcher = useCallback(
    (durationSeconds: number) => {
      if (typeof document === "undefined") {
        throw new Error("Monetag khÃ´ng kháº£ dá»¥ng trong mÃ´i trÆ°á»ng hiá»‡n táº¡i");
      }
      stopMonetagWatcher();

      return new Promise<void>((resolve, reject) => {
        monetagActiveRef.current = true;
        monetagElapsedRef.current = 0;
        setMonetagElapsed(0);
        setMonetagPaused(document.hidden ?? false);

        const handleVisibility = () => {
          setMonetagPaused(document.hidden ?? false);
        };

        const cleanup = () => {
          if (monetagTimerRef.current !== null) {
            window.clearInterval(monetagTimerRef.current);
            monetagTimerRef.current = null;
          }
          document.removeEventListener("visibilitychange", handleVisibility);
          monetagActiveRef.current = false;
          monetagCancelRef.current = null;
          monetagCleanupRef.current = null;
          setMonetagPaused(false);
        };

        const tick = () => {
          if (!monetagActiveRef.current) {
            return;
          }
          if (document.hidden) {
            return;
          }
          monetagElapsedRef.current += 1;
          setMonetagElapsed(monetagElapsedRef.current);
          if (monetagElapsedRef.current >= durationSeconds) {
            cleanup();
            resolve();
          }
        };

        document.addEventListener("visibilitychange", handleVisibility);
        monetagTimerRef.current = window.setInterval(tick, 1_000);
        monetagCleanupRef.current = cleanup;
        monetagCancelRef.current = (reason: Error) => {
          cleanup();
          reject(reason);
        };
        handleVisibility();
      });
    },
    [stopMonetagWatcher],
  );

  useEffect(() => {
    return () => {
      stopMonetagWatcher();
    };
  }, [stopMonetagWatcher]);

  const providerOptions = useMemo(() => {
    const providers = policy?.providers ?? {};
    const entries: Array<[string, RewardProviderConfig | undefined]> = [];

    Object.entries(providers).forEach(([key, cfg]) => {
      if (cfg?.enabled) {
        entries.push([key.toLowerCase(), cfg]);
      }
    });

    if (entries.length === 0) {
      entries.push([
        "monetag",
        (providers.monetag as RewardProviderConfig | undefined) ?? undefined,
      ]);
    }

    return entries;
  }, [policy]);

  const requiredDuration = policy?.requiredDuration ?? 30;
  const minIntervalSeconds = policy?.minInterval ?? 30;
  const monetagProgress =
    requiredDuration > 0
      ? Math.min(100, (monetagElapsed / requiredDuration) * 100)
      : 0;

  useEffect(() => {
    const enabledKeys = providerOptions.map(([value]) => value);
    if (enabledKeys.length === 0) {
      if (selectedProvider !== "monetag") {
        setSelectedProvider("monetag");
      }
      if (activeProvider !== "monetag") {
        setActiveProvider("monetag");
      }
      return;
    }
    const preferred = (policy?.defaultProvider ?? enabledKeys[0]).toLowerCase();
    if (!enabledKeys.includes(selectedProvider)) {
      setSelectedProvider(preferred);
    }
    if (!enabledKeys.includes(activeProvider)) {
      setActiveProvider(preferred);
    }
  }, [providerOptions, policy, selectedProvider, activeProvider]);

  const runImaAd = useCallback(
    async (adTagUrl: string) => {
      if (!adTagUrl) {
        throw new Error("Thiáº¿u ad tag cho Google IMA");
      }
      await ensureImaSdk();
      const google = window.google;
      const videoElement = videoRef.current;
      const containerElement = adContainerRef.current;
      if (!google?.ima || !videoElement || !containerElement) {
        throw new Error("Google IMA chÆ°a sáºµn sÃ ng");
      }

      return new Promise<void>((resolve, reject) => {
        const adDisplayContainer = new google.ima.AdDisplayContainer(
          containerElement,
          videoElement,
        );
        try {
          adDisplayContainer.initialize();
        } catch {
          /* ignore */
        }

        const adsLoader = new google.ima.AdsLoader(adDisplayContainer);
        adsLoader.addEventListener(
          google.ima.AdErrorEvent.Type.AD_ERROR,
          (event: any) => {
            adsLoader.destroy();
            reject(
              new Error(event.getError()?.toString() ?? "Lá»—i phÃ¡t quáº£ng cÃ¡o"),
            );
          },
          false,
        );

        adsLoader.addEventListener(
          google.ima.AdsManagerLoadedEvent.Type.ADS_MANAGER_LOADED,
          (event: any) => {
            try {
              const adsManager = event.getAdsManager(videoElement);
              adsManager.addEventListener(
                google.ima.AdEvent.Type.CONTENT_RESUME_REQUESTED,
                () => {
                  videoElement.pause();
                },
              );
              adsManager.addEventListener(
                google.ima.AdEvent.Type.STARTED,
                () => {
                  setStatus("playing");
                },
              );
              adsManager.addEventListener(
                google.ima.AdEvent.Type.COMPLETE,
                () => {
                  resolve();
                },
              );
              adsManager.addEventListener(
                google.ima.AdEvent.Type.ALL_ADS_COMPLETED,
                () => {
                  resolve();
                },
              );
              adsManager.addEventListener(
                google.ima.AdErrorEvent.Type.AD_ERROR,
                (errEvent: any) => {
                  reject(
                    new Error(
                      errEvent.getError()?.toString() ?? "Lá»—i phÃ¡t quáº£ng cÃ¡o",
                    ),
                  );
                },
              );
              adsManager.init(
                containerElement.clientWidth || 640,
                containerElement.clientHeight || 360,
                google.ima.ViewMode.NORMAL,
              );
              adsManager.start();
            } catch (error) {
              reject(error instanceof Error ? error : new Error(String(error)));
            }
          },
          false,
        );

        const request = new google.ima.AdsRequest();
        request.adTagUrl = adTagUrl;
        request.linearAdSlotWidth = containerElement.clientWidth || 640;
        request.linearAdSlotHeight = containerElement.clientHeight || 360;
        request.nonLinearAdSlotWidth = containerElement.clientWidth || 640;
        request.nonLinearAdSlotHeight =
          (containerElement.clientHeight || 360) / 3;
        request.setAdWillAutoPlay(true);
        request.setAdWillPlayMuted(false);

        try {
          adsLoader.requestAds(request);
        } catch (error) {
          reject(error instanceof Error ? error : new Error(String(error)));
        }
      });
    },
    [],
  );

  const waitForWalletUpdate = useCallback(
    async (previousBalance: number): Promise<number> => {
      for (let attempt = 0; attempt < 6; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 1_200));
        const result = await refetchWallet();
        const currentBalance = result.data?.balance ?? previousBalance;
        if (currentBalance > previousBalance) {
          return currentBalance;
        }
      }
      return previousBalance;
    },
    [refetchWallet],
  );

  const runMonetagFlow = useCallback(
    async (response: PrepareAdResponse, durationSeconds: number) => {
      if (typeof document === "undefined") {
        throw new Error("Monetag khÃ´ng kháº£ dá»¥ng trong mÃ´i trÆ°á»ng hiá»‡n táº¡i");
      }
      const container = monetagContainerRef.current;
      if (!container) {
        throw new Error("KhÃ´ng thá»ƒ khá»Ÿi táº¡o vÃ¹ng hiá»ƒn thá»‹ Monetag");
      }
      const zoneId =
        response.zoneId ?? policy?.providers?.monetag?.zoneId ?? null;
      const scriptUrl =
        response.scriptUrl ?? policy?.providers?.monetag?.scriptUrl ?? null;
      const ticket = response.ticket;
      if (!zoneId || !scriptUrl || !ticket) {
        throw new Error("Thiáº¿u cáº¥u hÃ¬nh Monetag tá»« mÃ¡y chá»§");
      }

      await ensureMonetagScript(scriptUrl);
      showMonetagAd(zoneId, container);
      setActiveProvider("monetag");
      setStatus("playing");
      setMessage("Giá»¯ tab nÃ y hiá»ƒn thá»‹ cho tá»›i khi tiáº¿n trÃ¬nh hoÃ n táº¥t.");

      const watchDuration = Math.max(1, Math.round(durationSeconds));

      try {
        await startMonetagWatcher(watchDuration);
      } catch (error) {
        throw error instanceof Error ? error : new Error(String(error));
      }

      try {
        setStatus("verifying");
        const result = await completeMonetagAd({
          nonce: response.nonce,
          ticket,
          durationSec: Math.max(
            watchDuration,
            Math.round(monetagElapsedRef.current),
          ),
          deviceHash: response.deviceHash,
          provider: response.provider,
        });
        if (!result.ok) {
          throw new Error("Há»‡ thá»‘ng khÃ´ng xÃ¡c nháº­n Ä‘Æ°á»£c lÆ°á»£t xem Monetag.");
        }
        return result;
      } finally {
        stopMonetagWatcher();
      }
    },
    [policy, startMonetagWatcher, stopMonetagWatcher],
  );

  const prepareMutation = useMutation(prepareRewardedAd);

  const handleWatchAd = useCallback(async () => {
    if (!profile) {
      setMessage("Báº¡n cáº§n Ä‘Äƒng nháº­p Ä‘á»ƒ nháº­n thÆ°á»Ÿng.");
      return;
    }
    if (!policy) {
      setMessage("KhÃ´ng thá»ƒ táº£i chÃ­nh sÃ¡ch pháº§n thÆ°á»Ÿng.");
      return;
    }
    if (cooldownUntil && cooldownUntil > Date.now()) {
      setStatus("error");
      setMessage(
        `Báº¡n Ä‘ang trong thá»i gian chá» ${formatSeconds(cooldownRemaining)}.`,
      );
      return;
    }

    setStatus("preparing");
    setMessage(null);

    const turnstileToken = await executeTurnstile().catch((error) => {
      console.warn("turnstile", error);
      return null;
    });

    const clientNonce = crypto.randomUUID();
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const signature =
      (await signPrepareRequest(
        profile.id,
        clientNonce,
        timestamp,
        PLACEMENT,
      )) ?? null;
    const hints = collectClientHints();
    const startingBalance = walletBalance;

    const providerChoice = (
      selectedProvider ||
      policy.defaultProvider ||
      providerOptions[0]?.[0] ||
      "monetag"
    ).toLowerCase();

    let prepareResponse: PrepareAdResponse;
    try {
      prepareResponse = await prepareMutation.mutateAsync({
        placement: PLACEMENT,
        provider: providerChoice,
        turnstileToken,
        clientNonce,
        timestamp,
        signature,
        hints,
      });
    } catch (error) {
      setStatus("error");
      if (error instanceof ApiError) {
        const detail =
          (error.data as { detail?: string })?.detail ?? error.message;
        setMessage(detail);
        if (detail?.toLowerCase().includes("cooldown")) {
          setCooldownUntil(Date.now() + minIntervalSeconds * 1000);
        }
      } else if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("KhÃ´ng thá»ƒ chuáº©n bá»‹ quáº£ng cÃ¡o. Vui lÃ²ng thá»­ láº¡i.");
      }
      return;
    }

    const effectiveProvider = (
      prepareResponse.provider ?? providerChoice
    ).toLowerCase();
    setActiveProvider(effectiveProvider);

    if (effectiveProvider === "monetag") {
      try {
        setStatus("loading");
        const result = await runMonetagFlow(
          prepareResponse,
          requiredDuration,
        );
        setStatus("success");
        const gained = Math.max(0, result.added ?? 0);
        if (gained > 0) {
          setMessage(`+${gained} xu Ä‘Ã£ Ä‘Æ°á»£c cá»™ng vÃ o vÃ­ cá»§a báº¡n.`);
        } else {
          setMessage("Quáº£ng cÃ¡o Ä‘Ã£ hoÃ n táº¥t. Sá»‘ dÆ° sáº½ Ä‘Æ°á»£c cáº­p nháº­t sá»›m.");
        }
        setCooldownUntil(Date.now() + minIntervalSeconds * 1000);
        refresh();
        refetchWallet();
        refetchMetrics();
      } catch (error) {
        setStatus("error");
        if (error instanceof Error) {
          setMessage(error.message);
        } else {
          setMessage("KhÃ´ng thá»ƒ hoÃ n thÃ nh quáº£ng cÃ¡o Monetag. Vui lÃ²ng thá»­ láº¡i.");
        }
      }
      return;
    }

    if (effectiveProvider === "gma") {
      try {
        setStatus("loading");
        setMessage(null);
        stopMonetagWatcher();
        if (!prepareResponse.adTagUrl) {
          throw new Error("Thiáº¿u ad tag cho Google IMA");
        }
        await runImaAd(prepareResponse.adTagUrl);
        setStatus("verifying");
        const newBalance = await waitForWalletUpdate(startingBalance);
        if (newBalance > startingBalance) {
          const gained = newBalance - startingBalance;
          setStatus("success");
          setMessage(`+${gained} xu Ä‘Ã£ Ä‘Æ°á»£c cá»™ng vÃ o vÃ­ cá»§a báº¡n.`);
        } else {
          setStatus("success");
          setMessage("Quáº£ng cÃ¡o Ä‘Ã£ hoÃ n táº¥t. Sá»‘ dÆ° sáº½ Ä‘Æ°á»£c cáº­p nháº­t sá»›m.");
        }
        setCooldownUntil(Date.now() + minIntervalSeconds * 1000);
        refresh();
        refetchWallet();
        refetchMetrics();
      } catch (error) {
        setStatus("error");
        if (error instanceof Error) {
          setMessage(error.message);
        } else {
          setMessage("KhÃ´ng thá»ƒ phÃ¡t quáº£ng cÃ¡o. Vui lÃ²ng thá»­ láº¡i.");
        }
      }
      return;
    }

    setStatus("error");
    setMessage("NhÃ  cung cáº¥p quáº£ng cÃ¡o khÃ´ng Ä‘Æ°á»£c há»— trá»£.");
  }, [
    profile,
    policy,
    cooldownUntil,
    cooldownRemaining,
    walletBalance,
    selectedProvider,
    providerOptions,
    prepareMutation,
    minIntervalSeconds,
    runMonetagFlow,
    requiredDuration,
    refresh,
    refetchWallet,
    refetchMetrics,
    stopMonetagWatcher,
    runImaAd,
    waitForWalletUpdate,
  ]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Xem quáº£ng cÃ¡o nháº­n thÆ°á»Ÿng</h1>
        <p className="text-muted-foreground">
          Xem quáº£ng cÃ¡o 30 giÃ¢y Ä‘á»ƒ nháº­n 5 xu. Pháº§n thÆ°á»Ÿng sáº½ Ä‘Æ°á»£c cá»™ng khi há»‡ thá»‘ng xÃ¡c minh thÃ nh cÃ´ng.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Nháº­n +5 xu</CardTitle>
            <CardDescription>
              Má»—i lÆ°á»£t xem há»£p lá»‡ sáº½ Ä‘Æ°á»£c cá»™ng xu sau khi xÃ¡c minh.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 rounded-lg border border-border/40 px-3 py-2">
                <span className="text-sm text-muted-foreground">Sá»‘ dÆ° hiá»‡n táº¡i</span>
                <Badge variant="secondary" className="text-base font-semibold">
                  {walletBalance} xu
                </Badge>
              </div>
              <div className="flex items-center gap-2 rounded-lg border border-border/40 px-3 py-2">
                <span className="text-sm text-muted-foreground">ThÆ°á»Ÿng má»—i lÆ°á»£t</span>
                <Badge variant="outline">{policy?.rewardPerView ?? 5} xu</Badge>
              </div>
            </div>

            {providerOptions.length > 1 && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Chá»n nhÃ  cung cáº¥p quáº£ng cÃ¡o</p>
                <RadioGroup
                  value={selectedProvider}
                  onValueChange={(value) => setSelectedProvider(value)}
                  className="flex flex-wrap gap-2"
                >
                  {providerOptions.map(([value, cfg]) => {
                    const id = `provider-${value}`;
                    return (
                      <div
                        key={value}
                        className={`flex items-center gap-2 rounded-md border border-border/40 px-3 py-2 transition ring-offset-background ${
                          selectedProvider === value ? "ring-1 ring-primary" : ""
                        }`}
                      >
                        <RadioGroupItem id={id} value={value} />
                        <div className="flex flex-col">
                          <Label htmlFor={id} className="text-sm font-medium">
                            {providerDisplayName(value)}
                          </Label>
                          <span className="text-xs text-muted-foreground">
                            {value === "monetag"
                              ? "Bá»™ Ä‘áº¿m phÃ­a client vÃ  vÃ© xÃ¡c minh"
                              : "Google IMA vÃ  xÃ¡c minh phÃ­a mÃ¡y chá»§"}
                          </span>
                          {value === "monetag" && cfg?.zoneId && (
                            <span className="text-xs text-muted-foreground">
                              Zone {cfg.zoneId}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </RadioGroup>
              </div>
            )}

            <div className="flex flex-col gap-3">
              <Button
                onClick={handleWatchAd}
                disabled={
                  prepareMutation.isLoading ||
                  status === "loading" ||
                  status === "playing" ||
                  status === "verifying" ||
                  (cooldownUntil !== null && cooldownUntil > Date.now())
                }
                className="w-fit"
              >
                {prepareMutation.isLoading || status === "loading" ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Äang chuáº©n bá»‹ quáº£ng cÃ¡o
                  </>
                ) : status === "playing" ? (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Quáº£ng cÃ¡o Ä‘ang cháº¡y
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Xem quáº£ng cÃ¡o (+{policy?.rewardPerView ?? 5} xu)
                  </>
                )}
              </Button>
              {cooldownUntil && cooldownUntil > Date.now() && (
                <div className="text-sm text-muted-foreground">
                  Vui lÃ²ng Ä‘á»£i {formatSeconds(cooldownRemaining)} trÆ°á»›c khi xem quáº£ng cÃ¡o tiáº¿p theo.
                </div>
              )}
            </div>

            <div className="rounded-lg border border-border/40 bg-muted/30 p-4">
              <div className="flex items-start gap-3">
                {status === "success" ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                ) : status === "error" ? (
                  <ShieldAlert className="h-5 w-5 text-destructive" />
                ) : (
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                )}
                <div>
                  <p className="text-sm font-semibold">
                    {status === "idle" && "Sáºµn sÃ ng nháº­n thÆ°á»Ÿng"}
                    {status === "preparing" && "Äang chuáº©n bá»‹ quáº£ng cÃ¡o..."}
                    {status === "loading" && "Äang táº£i quáº£ng cÃ¡o..."}
                    {status === "playing" && "Quáº£ng cÃ¡o Ä‘ang phÃ¡t, vui lÃ²ng xem háº¿t Ä‘á»ƒ nháº­n thÆ°á»Ÿng."}
                    {status === "verifying" && "Äang chá» xÃ¡c minh pháº§n thÆ°á»Ÿng..."}
                    {status === "success" && "HoÃ n táº¥t"}
                    {status === "error" && "KhÃ´ng thá»ƒ hoÃ n thÃ nh lÆ°á»£t xem"}
                  </p>
                  {message && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {message}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {activeProvider === "monetag" && (
              <div className="space-y-2">
                <Progress value={monetagProgress} />
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {Math.min(monetagElapsed, requiredDuration)}s / {requiredDuration}s
                  </span>
                  {monetagPaused && (
                    <span className="font-medium text-amber-500">
                      Giá»¯ tab nÃ y hiá»ƒn thá»‹
                    </span>
                  )}
                </div>
              </div>
            )}

            <div className="relative w-full overflow-hidden rounded-lg border border-border/40 bg-black aspect-video">
              <div
                ref={monetagContainerRef}
                className={`absolute inset-0 flex h-full w-full items-center justify-center transition-opacity ${
                  activeProvider === "monetag"
                    ? "opacity-100"
                    : "pointer-events-none opacity-0"
                }`}
              />
              <div
                ref={adContainerRef}
                className={`absolute inset-0 flex h-full w-full transition-opacity ${
                  activeProvider === "gma"
                    ? "opacity-100"
                    : "pointer-events-none opacity-0"
                }`}
              >
                <video
                  ref={videoRef}
                  className="h-full w-full object-contain"
                  playsInline
                  muted
                  controls={false}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card h-fit">
          <CardHeader>
            <CardTitle>Quota &amp; ChÃ­nh sÃ¡ch</CardTitle>
            <CardDescription>CÃ i Ä‘áº·t pháº§n thÆ°á»Ÿng hiá»‡n táº¡i</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {isLoadingPolicy && (
              <p className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Äang táº£i chÃ­nh sÃ¡ch...
              </p>
            )}
            {policy && (
              <ul className="space-y-2">
                <li>
                  <span className="font-medium">ThÆ°á»Ÿng má»—i lÆ°á»£t:</span>{" "}
                  {policy.rewardPerView} xu (xem tá»‘i thiá»ƒu {policy.requiredDuration}s)
                </li>
                <li>
                  <span className="font-medium">Thá»i gian chá»:</span>{" "}
                  {formatSeconds(policy.minInterval)} giá»¯a cÃ¡c lÆ°á»£t trÃªn cÃ¹ng thiáº¿t bá»‹.
                </li>
                <li>
                  <span className="font-medium">Giá»›i háº¡n theo ngÆ°á»i dÃ¹ng:</span>{" "}
                  {policy.effectivePerDay}/{policy.perDay} lÆ°á»£t má»—i ngÃ y.
                </li>
                <li>
                  <span className="font-medium">Giá»›i háº¡n theo thiáº¿t bá»‹:</span>{" "}
                  {policy.perDevice} lÆ°á»£t má»—i ngÃ y.
                </li>
                {policy.priceFloor !== null && (
                  <li>
                    <span className="font-medium">GiÃ¡ sÃ n hiá»‡n táº¡i:</span> CPM â‰¥ {policy.priceFloor}
                  </li>
                )}
              </ul>
            )}
            {!isLoadingPolicy && !policy && (
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-4 w-4" />
                KhÃ´ng thá»ƒ táº£i cáº¥u hÃ¬nh thÆ°á»Ÿng.{" "}
                <button
                  type="button"
                  onClick={() => refetchPolicy()}
                  className="underline"
                >
                  Thá»­ láº¡i
                </button>
              </div>
            )}

            <div className="border-t border-border/40 pt-4 space-y-1">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Thá»‘ng kÃª há»‡ thá»‘ng
              </p>
              <p>
                Tá»· lá»‡ láº¥p Ä‘áº§y:{" "}
                {metricsSnapshot.prepareOk
                  ? `${Math.round((metricsSnapshot.ssvSuccess / metricsSnapshot.prepareOk) * 100)}%`
                  : "--"}
              </p>
              <p>
                XÃ¡c minh SSV thÃ nh cÃ´ng: {metricsSnapshot.ssvSuccess} /{" "}
                {metricsSnapshot.ssvSuccess +
                  metricsSnapshot.ssvInvalid +
                  metricsSnapshot.ssvError +
                  metricsSnapshot.ssvDuplicate}
              </p>
              <p>Tá»•ng xu Ä‘Ã£ thÆ°á»Ÿng: {metricsSnapshot.rewardCoins}</p>
              <p>
                Tá»· lá»‡ lá»—i: {(metricsSnapshot.failureRatio * 100).toFixed(1)}%
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Earn;
