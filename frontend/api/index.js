const axios = require('axios');

// Replace with your deployed backend URL
const BACKEND_URL = process.env.BACKEND_URL || 'https://your-backend-url.railway.app';

export default async function handler(req, res) {
  try {
    const { method, url, body, headers } = req;
    
    // Remove /api prefix from the URL
    const apiPath = url.replace('/api', '');
    
    // Forward the request to your backend
    const response = await axios({
      method,
      url: `${BACKEND_URL}${apiPath}`,
      data: body,
      headers: {
        ...headers,
        'host': new URL(BACKEND_URL).host
      },
      responseType: 'stream'
    });
    
    // Forward the response
    res.status(response.status);
    Object.keys(response.headers).forEach(key => {
      res.setHeader(key, response.headers[key]);
    });
    
    response.data.pipe(res);
  } catch (error) {
    console.error('API Proxy Error:', error);
    res.status(500).json({ 
      error: 'Internal Server Error',
      message: error.message 
    });
  }
} 