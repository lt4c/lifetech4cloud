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

async function checkToken(token) {
  if (!token || typeof token !== "string") {
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
    // Gọi end_task trước để dọn trạng thái nếu có (không fail toàn bộ nếu lỗi)
    try {
      await postWithRetry(endUrl, "{}", { headers });
    } catch (_) {}

    const res = await postWithRetry(checkUrl, "{}", { headers });
    const data = res?.data || {};
    const limit = data.task_course_usage_limit;
    const remaining = data.task_course_usage_remaining;

    if (typeof limit === "number" && typeof remaining === "number") {
      const limitHours = Math.floor(limit / 3600000);
      const remainingHours = Math.floor(remaining / 3600000);
      return { valid: true, limitHours, remainingHours };
    }
    return { valid: false, error: "invalid_or_expired" };
  } catch (err) {
    if (err && err.response && err.response.status) {
      return { valid: false, error: `http_${err.response.status}` };
    }
    return { valid: false, error: "connection_error" };
  }
}

module.exports = { checkToken };

