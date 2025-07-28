// 新增配置文件
export const API_CONFIG = {
  BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'https://api.yourdomain.com' 
    : 'http://localhost:8000',
  ENDPOINTS: {
    PROCESS_ANALYSIS: '/process'
  }
}