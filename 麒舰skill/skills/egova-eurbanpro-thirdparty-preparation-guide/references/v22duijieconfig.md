**V22市区对接采集配置文档**

目录

[1. 授权配置 3](#_Toc173515134)

[1.1. 新增对接应用 3](#_Toc173515135)

[1.2. 对接系统表（API\_SYS\_INFO）表配置 4](#_Toc173515136)

[1.3. 对接代理人（AGENT\_USERNAME） 6](#_Toc173515137)

[1.4. 第三方调用接口获取Token 8](#_Toc173515138)

[1.5. 免密场景 9](#_Toc173515139)

[2. 接口采集配置 10](#_Toc173515140)

[2.1. 采集阶段、参与者、流程配置（API\_SYS\_ACTION\_TRIGGER） 10](#_Toc173515141)

[2.2. 采集问题来源限制（API\_SYS\_TRIGGER\_EVENT\_SRC） 13](#_Toc173515142)

[2.3. 采集参与者限制（API\_SYS\_TRIGGER\_PART） 14](#_Toc173515143)

[3. 采集推送配置 14](#_Toc173515144)

[3.1. 推送地址配置（API\_SYS\_ACTION\_INFO） 14](#_Toc173515145)

[3.2. 开启即时推送 15](#_Toc173515146)

# 授权配置

V22系统的内置所有对接接口都不支持免密访问了，需要先为对接方提供授权认证参数，对接方根据市区对接接口文档中的授权认证接口获取token后才能调用V22对接接口。

## 新增对接应用

在V22系统或用户中心的应用管理中新增应用。

![](data:image/png;base64...)

![](data:image/png;base64...)

新增后查看应用，即可获得认证参数clientId和clientSecret。

![](data:image/png;base64...)

## 对接系统表（API\_SYS\_INFO）表配置

完成对接应用添加后，在对接系统表新增一条记录。

![](data:image/png;base64...)

字段说明：

* code：即应用编码。
* name：对接方名字。
* sys\_client\_id：即1.1新增应用中的client\_id。
* client\_id：即1.1新增应用中的client\_id。
* client\_secret：即1.1新增应用中的client\_secret。
* valid\_flag：是否有效。
* retry\_num：该对接平台的重推次数。
* agent\_username：对接代理人，在下节详细解释。
* local\_flag：是否本地平台，整个表里只允许一条记录为1。
* auto\_assign\_flag：对接方上报案件后，是否由匹配的工作流参与者自动办理案件。

**添加完成后需调用接口刷新对接配置。**使用postman调用，认证请求头复制v22里任意接口调用的

v22-api//unity/openapi/config/clear-sys-config

![](data:image/png;base64...)

![](data:image/png;base64...)

## 对接代理人（AGENT\_USERNAME）

对接代理人字段对应的是人员登录名，即userName。

![](data:image/png;base64...)

表示该对接方调用我方平台所有对接接口时，都以此对接代理人的账号信息作为虚拟操作人。比如案件上报，显示的登记人是此对接账号。

![](data:image/png;base64...)

第三方调用办结接口通知我方办结时，显示的办结操作人也是对接账号。

![](data:image/png;base64...)

需要第三方推送已下派案件的办理经过到我方平台时，使用标准的办理经过同步接口显示的操作人和操作部门都会是这个固定的对接账号和对接账号所属部门。部分情况下不太合理，有办理经过同步自定义操作人和操作部门需求的，目前只能由研发在星桥处理，直接插入办理经过表wf\_item\_inst，或插入办理经过扩展表mis\_item\_list。

第三方需要使用接口进行案件流程操作，如申请授权、答复授权、办结案件、作废案件、核查反馈等，**请确保对接账号人员具有相应的岗位权限**。

比如案件派遣到专业部门阶段的某个参与者，推送到第三方平台。第三方进行处置反馈时需要对接代理人有该参与者权限才能正常处置反馈。

![](data:image/png;base64...)![](data:image/png;base64...)

答复授权需要对接账号有答复权限。

![](data:image/png;base64...)

![](data:image/png;base64...)

## 第三方调用接口获取Token

提供client\_id和client\_secret后，第三方即可通过认证接口获取token，认证方式详见接口文档。

![](data:image/png;base64...)

如果上述配置均已配置完成，但调用获取token接口提示**代理用户认证失败**，需要检查用户中心配置，服务名需要与麒舰系统的服务名保持一致。麒舰系统的服务名可到nacos或麒舰系统的配置文件查看。

![](data:image/png;base64...)

![](data:image/png;base64...)

**--egova.service.client-agent.name=egova-urbanpro-hotline-service**

## 免密场景

某些场景下必须使用免密接口，请使用星桥代理V22对接接口，到授权认证脚本自行处理认证，脚本示例如下：

|  |
| --- |
| import org.bouncycastle.asn1.gm.GMNamedCurves;  import org.bouncycastle.asn1.x9.X9ECParameters;  import org.bouncycastle.crypto.engines.SM2Engine;  import org.bouncycastle.crypto.params.ECDomainParameters;  import org.bouncycastle.crypto.params.ECPublicKeyParameters;  import org.bouncycastle.crypto.params.ParametersWithRandom;  import org.bouncycastle.math.ec.ECPoint;  import org.bouncycastle.util.encoders.Hex;  import java.nio.charset.StandardCharsets;  // 获取公钥  var pubKeyRes = com.egova.api.util.http.HttpUtils.get('http://99.99.24.98:8080/v22-api/oauth/extras/openapi/pubkey', String.class);  var pubKeyMap = com.egova.json.utils.JsonUtils.deserialize(pubKeyRes.getBody(), Map.class);  var hexPubKey = pubKeyMap.message  //私钥加密 即client\_secret  var src = 'e65ee4f21c'  var client\_secret = Hex.toHexString(encrypt(src.getBytes(StandardCharsets.UTF\_8), hexPubKey));  //获取token  var postMap = [  'client\_id':'1778685023958671360',  'client\_secret':client\_secret,  'grant\_type':'client\_credentials',  'uid':java.util.UUID.randomUUID().toString(),  ]  var tokenRes = com.egova.api.util.http.HttpUtils.postJson('http://99.99.24.98:8080/v22-api/oauth/extras/openapi/client', com.egova.json.utils.JsonUtils.serialize(postMap), String.class);  var tokenMap = com.egova.json.utils.JsonUtils.deserialize(tokenRes.getBody(), Map.class);  variables['egova\_openapi\_token'] = tokenMap.result.token.access\_token;  request.setQueryParam('egova\_openapi\_token', tokenMap.result.token.access\_token);  def encrypt(byte[] src, String hexPubKey) {  X9ECParameters pubParameters = GMNamedCurves.getByName("sm2p256v1");  ECDomainParameters pubDomainParameters = new ECDomainParameters(pubParameters.getCurve(),  pubParameters.getG(), pubParameters.getN());  ECPoint pubPoint = pubParameters.getCurve().decodePoint(Hex.decode(hexPubKey));  ECPublicKeyParameters encryptPubKey = new ECPublicKeyParameters(pubPoint, pubDomainParameters);  try {  SM2Engine sm2Engine = new SM2Engine(SM2Engine.Mode.C1C3C2);  ParametersWithRandom parametersWithRandom = new ParametersWithRandom(encryptPubKey);  sm2Engine.init(true, parametersWithRandom);  return sm2Engine.processBlock(src,0,src.length);  }catch (Exception e) {  throw new RuntimeException("");  }  } |

# 接口采集配置

## 采集阶段、参与者、流程配置（API\_SYS\_ACTION\_TRIGGER）

![](data:image/png;base64...)

在api\_sys\_action\_trigger表配置，配置后在特定阶段的特定参与者进行某操作时，会记录一次对接推送记录，可通过配置推送地址直接推送给第三方，或第三方调用通知查询接口查询到该记录。字段解释：

* sys\_code：对接平台编码，同api\_sys\_info的应用编码code。
* action/action\_name：采集的操作名，现在支持如下操作：
  + REPORT\_NOTICE：案件下派通知，即批转至某阶段时采集案件基本信息。
  + ITEM\_INST\_SYNC\_NOTICE：办理经过通知，批转至某阶段时采集案件流程信息。
  + APPLY\_ARCHIVE\_NOTICE：申请办结通知，申请办结时采集申请信息。
  + REPLY\_FINISH\_NOTICE：答复办结通知，答复办结时采集答复信息。
  + APPLY\_CANCEL\_NOTICE：申请作废通知，申请作废时采集申请信息。
  + REPLY\_CANCEL\_NOTICE：答复作废通知，答复作废时采集答复信息。
  + APPLY\_POSTPONE\_NOTICE：申请延期通知，申请延期时采集申请信息。
  + REPLY\_POSTPONE\_NOTICE：答复延期通知，答复延期时采集答复信息。
  + APPLY\_ROLLBACK\_NOTICE：申请回退通知，申请回退时采集申请信息。
  + REPLY\_ROLLBACK\_NOTICE：答复回退通知，答复回退时采集答复信息。
  + FINISH\_NOTICE：办结通知，案件办结时采集办结信息。
  + CANCEL\_NOTICE：作废通知，案件作废是采集作废信息。
  + DISPOSE\_FEEDBACK\_NOTICE：处置反馈通知，案件完成处置时采集处置信息。
  + NOTIFY\_NOTICE：告知通知，案件完成受理办理告知时采集告知信息。
  + NOTICE\_SIGNING：签收通知，案件签收时采集签收信息。
* act\_def\_id/act\_property\_id/proc\_def\_id：采集的阶段标识、阶段属性、流程标识，获取方式见下图。

![](data:image/png;base64...)

* biz\_id：业务标识，同案件表mis\_rec的biz\_id。
* valid\_flag：是否开启采集。

有几类操作的采集配置需注意，办结操作的采集阶段是finish\_开头的结束节点。

![](data:image/png;base64...)

答复授权的采集流程、采集阶段是授权子流程中的流程标识和阶段标识。而申请授权的流程和采集阶段还是主流程中的流程标识和阶段标识。

![](data:image/png;base64...)

## 采集问题来源限制（API\_SYS\_TRIGGER\_EVENT\_SRC）

在API\_SYS\_TRIGGER\_EVENT\_SRC表配置采集器在哪些问题来源的情况下会采集推送，必须配置。

![](data:image/png;base64...)

* trigger\_id：采集器标识，对应API\_SYS\_ACTION\_TRIGGER表的id。
* event\_src\_id：问题来源标识，0表示所有的问题来源都采集。
* valid\_flag：是否启用。

## 采集参与者限制（API\_SYS\_TRIGGER\_PART）

在API\_SYS\_TRIGGER\_EVENT\_SRC表配置采集器在哪些问题来源的情况下会采集推送，必须配置。

![](data:image/png;base64...)

* trigger\_id：采集器标识，对应API\_SYS\_ACTION\_TRIGGER表的id。
* part\_id：参与者标识，0表示该阶段所有的参与者参与的案件都采集。
* valid\_flag：是否启用。

## 采集配置检查（API\_MESSAGE\_SEND）

系统上执行对应的操作后，采集是否成功可到API\_MESSAGE\_SEND表和API\_MESSAGE\_SEND\_HIS表查看是否有新增记录。

![](data:image/png;base64...)

# 采集推送配置

## 推送地址配置（API\_SYS\_ACTION\_INFO）

若采集对接信息进入表的同时需要调用第三方接口推送相关信息，需要到API\_SYS\_ACTION\_INFO配置该对接平台该操作推送的接口地址。

![](data:image/png;base64...)

* sys\_code：对接平台编码，对应API\_SYS\_INFO表的CODE。
* action/action\_name：采集操作名，对应api\_sys\_action\_trigger表的action。
* api\_url：接口地址，需V22系统部署的服务器可访问。接口地址为第三方系统提供时，此处一般配置星桥地址，在前置后置脚本做转换处理；公司内部系统对接时可直接配置其他系统的V22服务对接接口地址。
* request\_type：请求方式，一般用POST。
* retry\_num：失败重试次数，开启定时任务才会用到。

## 开启即时推送

将API\_SYS\_CONFIG\_ITEM表的OPEN\_ACTION\_TRIGGER\_FLAG置为1。

![](data:image/png;base64...)