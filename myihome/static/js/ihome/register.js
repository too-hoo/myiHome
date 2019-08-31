// 读取cookie的方法,通过正则表达式拿到的match类似python, \转义, \b 表示单词的边界, 接着根据传入的name拼接,([^;]*)表示一个组,
// [^;]表示结尾不是分号,一个或者多个都可以,最后以\b表示边界结尾,
// "csrf_token=IjBiYTQzZDdjY2VkNmZiMmIwZDEzYTdjMzJhZTcyNWNkMDAyOGMwZmUi.XWniag.GSnm_bxR7TKAwjpChQz7-MuCa7k"
//  最后返回的是一个列表
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    // 三元表达式,真:返回列表第1号元素r[1](1号是值,0号是键), 假:undefined(没定义没见过的意思),相当于None
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
            alert(resp.errmsg)
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
    // 如果光标在输入框里面的话错误信息会隐藏
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
    // 为表单的提交补充自定义的函数行为(提交事件e)(浏览器提交的格式是Form的键值对,但是后端接收的是json格式的数据,所以要禁止)
    $('.form-register').submit(function (event) {
        // 阻止浏览器自己默认的提交表单事件,其不会默认自己发送
        event.preventDefault();
        // 获取后端需要的数据，电话号，短信验证码，密码
        var phone_num=$('#mobile').val(),
            phonecode=$('#phonecode').val(),
            password=$('#password').val(),
            password2=$('#password2').val(),
            regix=/^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}$/;
        // 判断是否为空,并校验
        if(!regix.exec(phone_num)){
            $('#mobile-err span').text('手机号错误'); //.html('手机号错误'); 也行
            $('#mobile-err').show();
            // return;
        }
        if(!phonecode) {
            $('#phone-code-err span').text('手机验证码不能为空！');
            $('#phone-code-err').show();
            // return;
        }
        if(!password){
            $('#password-err span').text('密码不能为空!');
            $('#password-err').show();
            // return;
        }
        if(password != password2){
            $('#password-err span').text('两次密码不一致!');
            $('#password-err').show();
            // return;
        }
        //组织参数
        var params={
            'phone_num':phone_num,  //电话号码
            'sms_code':phonecode,  //短信验证码
            'password':password,     //密码1
            'password2':password2     //密码2
        };
        //提交表单
        $.ajax({
            url:'/api/v1.0/users',
            type:'post',
            data:JSON.stringify(params), //将参数params转化成为json数据
            contentType:'application/json',
            // 通过request请求体往外拿数据的两种方式:(data模式包括json,xml等)request.data和(form模式)request.form.get("csrf_token")
            // 这里请求体的是json格式不是表单,如果请求体的数据不是表单格式,将csrf_token的值可以放到请求头中:X-CSRFToken,
            headers:{ // 由浏览器的同源策略,这里是可以操作cookie的, 后端会识别X-CSRFToken关键字
                'X-CSRFToken':getCookie('csrf_token')
            }, // 请求头,将csrf_token值放到请求头中, 方便后端csrf进行验证
            dataType:"json",
            success:function(resp){
                if(resp.errno=='0'){
                    // 成功跳转到首页
                    alert(resp.errmsg);
                    location.href='/'   // 注册成功之后跳转到主页
                }else {
                    alert(resp.errmsg)
                }
            }
        });
    });
});
