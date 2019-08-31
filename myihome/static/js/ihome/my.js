function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

//点击退出按钮时执行的函数
function logout() {
    $.ajax({
        url:'/api/v1.0/sessions',
        type:'delete',  //delete 请求方法也是会被CSRF拦截的, 所以是需要加上CSRF参数的
        headers:{'X-CSRFToken':getCookie('csrf_token')},
        success:function (res) {
            if(res.errno=='0'){
                // alert(res.errmsg);
                location.href='/'
            }else {
                alert(res.errmsg)
            }
        }
    });
}

$(document).ready(function(){

    //  在页面加载完毕之后去加载个人信息
    $.get('/api/v1.0/users',function (res) {
        if(res.errno=='0'){
            // 加载头像
            $('#user-avatar').attr('src',res.user.avatar_url);
            $('#user-name').text(res.user.name);
            $('#user-mobile').text(res.user.phone_num);
        }else if (res.re_code=='4101'){
            // 未登录，跳转到首页
            location.href='/'
        }else {
            alert(res.msg)
        }
    });
});
