function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 前端产生uuid的方法
function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}
// 保存图片验证码编号(使用uuid原因是不易重复,使用时间戳可能会冲突重复)
var imageCodeId = ""

// 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
function generateImageCode() {
    // 形成图片验证码的后端地址,设置到页面中,让浏览器请求验证码图片
    //1.生成图片验证码编号(UUID)
    imageCodeId =generateUUID();
    // 设置图片的url
    var url='/api/v1.0/image_codes/' + imageCodeId;   //拼接请求地址
    // 使用>选择div下面的img元素,中间使用空格也是可以.image-code img
    $('.image-code>img').attr('src',url);  //设置img的src属性
    $("#imagecode").val(""); // 刷新验证码时候清空输入框$("#name").val("");
}

function sendSMSCode() {
    // 校验参数，保证输入框有数据填写
    $(".phonecode-a").removeAttr("onclick");
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    // TODO: 通过ajax方式向后端接口发送请求，让后端发送短信验证码
    var phone_num=$('#mobile').val();
    // 构造向后端请求的参数
    var params={
        'image_code_id':imageCodeId, //图片验证码的编号,(全局变量)
        'image_code':imageCode // 图片验证码的值
    };
    // 向后端发送请求
    $.get("/api/v1.0/sms_codes/" + phone_num, params, function (resp) {
        // resp是后端返回的响应值,因为后端返回的是json字符串,
        // 所以ajax帮助我们把这个json字符串转换成为js对象,resp就是转换后的对象
        if (resp.errno == "0"){
            var $time = $(".phonecode-a"); //选取对应的元素,使用$time存放
            var duration  = 60;
            // 表示发送成功
            var timer = setInterval(function () {
                $time.html(duration + "秒");
                if (duration === 1){
                    clearInterval(timer)
                    $time.html('获取验证码');
                    $(".phonecode-a").attr("onclick", "sendSMSCode();");
                }
                duration = duration - 1;
            }, 1000, 60)
        } else {
            $("#image-code-err span").html(resp.errmsg); // 下面显示提示信息
            $("#image-code-err").show();
            if ("4001" == resp.errno || "4002" == resp.errno) {
                    generateImageCode();
            }
            $(".phonecode-a").attr("onclick", "sendSMSCode();");
        }
    },'json');
}

$(document).ready(function() {
    generateImageCode();  // 生成一个图片验证码的编号，并设置页面中图片验证码img标签的src属性
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });

    // TODO: 注册的提交(判断参数是否为空)
    $('.form-register').submit(function (event) {
        // 阻止自己默认的提交表单事件
        event.preventDefault();
        // 获取后端需要的数据，电话号，密码，短信验证码
        var phone_num=$('#mobile').val(),
            phonecode=$('#phonecode').val(),
            password=$('#password').val(),
            regix=/^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}$/;
        // 判断是否为空,校验
        if(!regix.exec(phone_num)){
            $('#mobile-err span').text('手机号错误');
            $('#mobile-err').show()
        }
        if(!phonecode) {
            $('#phone-code-err span').text('手机验证码不能为空！');
            $('#phone-code-err').show();
        }
        if(!password){
            $('#password-err span').text('密码不能为空!');
            $('#password-err').show()
        }
        //组织参数
        var params={
            'phone_num':phone_num,
            'phonecode':phonecode,
            'password':password
        };
        提交表单
        $.ajax({
            url:'/api/1.0/users',
            type:'post',
            data:JSON.stringify(params),
            contentType:'application/json',
            headers:{'X-CSRFToken':getCookie('csrf_token')},
            success:function(response){
                if(response.re_code=='0'){
                    // 成功跳转到首页
                    alert(response.msg);
                    location.href='/'
                }else {
                    alert(response.msg)
                }
            }
        });
    });
});
