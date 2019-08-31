function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    //  添加登录表单提交操作
    $(".form-login").submit(function(e){
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        var params={
            'phone_num':mobile,
            'password':passwd
        };
        $.ajax({
                    url:'/api/v1.0/sessions',
                    type:'post',
                    data:JSON.stringify(params),
                    contentType:'application/json',
                    headers:{'X-CSRFToken':getCookie('csrf_token')},
                    success:function(response){
                        if(response.errno=='0'){
                            // 登录成功, 跳转到主页
                            location.href='/'
                        }else {
                            // 其他错误信息,在页面中显示
                            //alert(response.errmsg)
                            $("#password-err span").html(response.errmsg);
                            $("#password-err").show();
                        }
                    }
                });
    });
});
