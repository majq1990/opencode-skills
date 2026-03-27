/**
 * 钉钉API调试脚本
 */

const DINGTALK_API_BASE = 'https://api.dingtalk.com/v1.0';
const DINGTALK_OAPI_BASE = 'https://oapi.dingtalk.com';

async function debug() {
  const appKey = process.env.DINGTALK_APPKEY;
  const appSecret = process.env.DINGTALK_APPSECRET;

  console.log('=== 钉钉API调试 ===\n');
  console.log('AppKey:', appKey);
  console.log('AppSecret:', appSecret ? appSecret.substring(0, 10) + '...' : 'undefined');
  console.log();

  try {
    // 1. 获取 access_token
    console.log('1. 获取 access_token...');
    const tokenUrl = `${DINGTALK_OAPI_BASE}/gettoken?appkey=${appKey}&appsecret=${appSecret}`;
    const tokenResponse = await fetch(tokenUrl);
    const tokenData = await tokenResponse.json();
    console.log('响应:', JSON.stringify(tokenData, null, 2));
    
    if (tokenData.errcode !== 0) {
      console.error('获取token失败');
      return;
    }

    const accessToken = tokenData.access_token;
    console.log('access_token:', accessToken.substring(0, 20) + '...');
    console.log();

    // 2. 获取知识库列表
    console.log('2. 获取知识库列表...');
    const kbUrl = `${DINGTALK_API_BASE}/wiki/knowledgeBase/list?size=100`;
    console.log('请求URL:', kbUrl);
    
    const kbResponse = await fetch(kbUrl, {
      headers: {
        'x-acs-dingtalk-access-token': accessToken
      }
    });
    
    console.log('响应状态:', kbResponse.status, kbResponse.statusText);
    const kbData = await kbResponse.json();
    console.log('响应内容:', JSON.stringify(kbData, null, 2));
    console.log();

    // 3. 测试其他API
    console.log('3. 测试企业信息...');
    const corpUrl = 'https://oapi.dingtalk.com/topapi/v2/user/get?userid=1';
    const corpResponse = await fetch(corpUrl, {
      method: 'POST',
      headers: {
        'x-acs-dingtalk-access-token': accessToken,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    });
    const corpData = await corpResponse.json();
    console.log('用户API响应:', JSON.stringify(corpData, null, 2));

  } catch (error) {
    console.error('错误:', error.message);
    console.error(error.stack);
  }
}

debug();