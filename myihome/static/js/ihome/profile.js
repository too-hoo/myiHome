function showSuccessMsg() {
    // 显示成功信息,是整个页面变成一个弹框显示
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    // TODO: 在页面加载完毕向后端查询用户的信息
    $.get('/api/v1.0/users',function (res) {
        if(res.errno=='0'){
            $('#user-avatar').attr('src',res.user.avatar_url);
            $('#user-name').val(res.user.name)
        }else if(res.errno=='4101'){
            location.href='/'
        }else {
            alert(res.errmsg)
        }
    });
    // TODO: 管理上传用户头像表单的行为
    $('#form-avatar').submit(function (event) {
        // 阻止表单的默认行为
        event.preventDefault();
        // 使用jquery.form.min.js 提供的ajaxSubmit对表单进行异步提交
        $(this).ajaxSubmit({   // 这个和之前的使用完整的ajax请求是完全一样的
            url:'/api/v1.0/users/avatar',
            type:'post',
            dataType:"json",
            headers:{'X-CSRFToken':getCookie('csrf_token')},
            success:function (res) {
                if(res.errno=='0'){
                    // 表示上传成功
                    showSuccessMsg();
                    $('#user-avatar').attr('src',res.data.avatar_url)
                }else if(res.errno=='4101'){
                    // session异常就跳转到首页
                    location.href='/'
                }else {
                    alert(res.errmsg)
                }
            }
        });
    });
    //  管理用户名修改的逻辑
    $('#form-name').submit(function (event) {
         $('.error-msg').hide();
        // 删除默认提交行为
        event.preventDefault();
        //获取用户名,并转化成为json传到后台
        var name=$('#user-name').val();
        if(!name){
            alert('用户名不能为空！');
            return;
        }
        $.ajax({
            url:'/api/v1.0/users',
            type:'put',   // 注意请求方法是不一样的
            data:JSON.stringify({'name':name}),
            headers:{'X-CSRFToken':getCookie('csrf_token')},
            contentType:'application/json',
            success:function (res) {
                if(res.errno=='0'){
                    alert(res.errmsg)
                    showSuccessMsg();
                }else if(res.errno=='4101'){
                    location.href='/'
                }else {
                    $('.error-msg').show();  // 报错用户名已经存在
                }
            }
        });
    });
});

