const axios = require("axios");

async function checkToken(token) {
  if (!token || typeof token !== 'string') {
    return { valid: false, error: 'missing_token' };
  }

  const url = "https://learn.learn.nvidia.com/courses/course-v1:DLI+S-ES-01+V1/xblock/block-v1:DLI+S-ES-01+V1+type@nvidia-dli-platform-gpu-task-xblock+block@f373f5a2e27a42a78a61f699899d3904/handler/check_task";
  const headers = {
    accept: "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    cookie: `sessionid=${token}; edxloggedin=true; openedx-language-preference=en;`,
  };

  try {
    const res = await axios.post(url, "{}", { headers });
    const data = res.data;
    if (data && data.task_course_usage_limit && data.task_course_usage_remaining) {
      const limitHours = Math.floor(data.task_course_usage_limit / 3600000);
      const remainingHours = Math.floor(data.task_course_usage_remaining / 3600000);
      return { valid: true, limitHours, remainingHours };
    }
    return { valid: false, error: 'invalid_or_expired' };
  } catch (err) {
    if (err && err.response) {
      return { valid: false, error: `http_${err.response.status}` };
    }
    return { valid: false, error: 'connection_error' };
  }
}

module.exports = { checkToken };

