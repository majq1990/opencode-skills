import com.egova.json.utils.JsonUtils

// 返回推送结果和推送报文，便于联调排查
return JsonUtils.serialize([
    scene     : variables['pushScene'],
    targetPath: variables['pushTargetPath'],
    request   : variables['pushRequest'],
    result    : variables['pushResult']
])
