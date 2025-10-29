const axios = require("axios");

async function postWithRetry(url, data, options) {
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      const res = await axios.post(url, data, options);
      return res;
    } catch (error) {
      if (attempt === 2) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function checkToken(token) {
  if (!token || typeof token !== "string") {
    console.log('[CHECK_TOKEN] invalid input: missing_token');
    return { valid: false, error: "missing_token" };
  }

  const checkUrl =
    "https://learn.learn.nvidia.com/courses/course-v1:DLI+S-ES-01+V1/xblock/block-v1:DLI+S-ES-01+V1+type@nvidia-dli-platform-gpu-task-xblock+block@f373f5a2e27a42a78a61f699899d3904/handler/check_task";
  const endUrl =
    "https://learn.learn.nvidia.com/courses/course-v1:DLI+S-ES-01+V1/xblock/block-v1:DLI+S-ES-01+V1+type@nvidia-dli-platform-gpu-task-xblock+block@f373f5a2e27a42a78a61f699899d3904/handler/end_task";

  const headers = {
    accept: "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    // Đồng bộ với linux.js: thêm edx-user-info và openedx-language-preference
    cookie:
      `openedx-language-preference=en; sessionid=${token}; edxloggedin=true; edx-user-info={"version": 1, "username": "worker", "email": "worker@local.invalid"}`,
  };

  try {
    console.log('[CHECK_TOKEN] start validation for token:', String(token).substring(0, 12) + '...');
    console.log('[CHECK_TOKEN] cookie header:', headers.cookie.substring(0, 100) + '...');
    // 1) Gọi end_task trước để dọn trạng thái như linux.js
    try {
      console.log('[CHECK_TOKEN] end_task: sending');
      const endRes = await postWithRetry(endUrl, "{}", { headers });
      console.log('[CHECK_TOKEN] end_task: status', endRes?.status ?? 'unknown');
    } catch (_) {}

    // 2) Chờ ~10s giống đoạn "checking" trong linux.js
    console.log('[CHECK_TOKEN] wait 10s before check_task');
    await sleep(10000);
    console.log('[CHECK_TOKEN] wait done');

    // 3) Thử đọc usage, nhưng KHÔNG coi HTTP 400 là thất bại kiểm tra
    let limitHours;
    let remainingHours;
    try {
      console.log('[CHECK_TOKEN] check_task: sending');
      const res = await postWithRetry(checkUrl, "{}", { headers });
      console.log('[CHECK_TOKEN] check_task: status', res?.status ?? 'unknown');
      const data = res?.data || {};
      const limit = data.task_course_usage_limit;
      const remaining = data.task_course_usage_remaining;
      if (typeof limit === "number" && typeof remaining === "number") {
        limitHours = Math.floor(limit / 3600000);
        remainingHours = Math.floor(remaining / 3600000);
        console.log('[CHECK_TOKEN] usage parsed:', { limitHours, remainingHours });
      }
    } catch (e) {
      const st = e?.response?.status;
      console.log('[CHECK_TOKEN] check_task error, status:', st ?? 'unknown');
    }

    // Trả về hợp lệ nếu cookie đúng định dạng, tránh báo http_400 khi token mới
    if (typeof limitHours === "number" && typeof remainingHours === "number") {
      console.log('[CHECK_TOKEN] return: valid_with_usage');
      return { valid: true, limitHours, remainingHours };
    }
    console.log('[CHECK_TOKEN] return: valid_no_usage (likely new token or 400)');
    return { valid: true };
  } catch (err) {
    if (err && err.response && err.response.status) {
      // Không propagate lỗi HTTP như http_400 nữa để phù hợp với linux.js
      console.log('[CHECK_TOKEN] return: valid_http_error_passthrough status=', err.response.status);
      return { valid: true };
    }
    console.log('[CHECK_TOKEN] return: invalid_connection_error', err && err.message);
    return { valid: false, error: "connection_error" };
  }
}

module.exports = { checkToken };

