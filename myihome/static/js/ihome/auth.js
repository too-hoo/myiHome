function showSuccessMsg() {
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

$(document).ready(function(){
    // TODO: 查询用户的实名认证信息
    $.get('/api/v1.0/users/auth',function (res) {
        if(res.errno=='0'){
            // 认证只能一次，
            $('#real-name').val(res.user_auth.real_name);
            $('#id-card').val(res.user_auth.id_card);
            if(res.user_auth.real_name && res.user_auth.id_card){
                //如果查询有数据就不能修改。input框变不可选,保存按钮隐藏
                $('#real-name').attr('disabled','disabled');
                $('#id-card').attr('disabled','disabled');
                $('.btn-success').hide();
            }
        }else if(res.errno=='4101'){
            location.href='/'
        }else {
            alert(res.errmsg)
        }
    });

    // TODO: 管理实名信息表单的提交行为
    $('#form-auth').submit(function (event) {
         $('.error-msg').hide();
         // 阻止浏览器的默认提交
        event.preventDefault();
        // 获取方框中的值
        var real_name=$('#real-name').val(),
            id_card=$('#id-card').val();
        var params={
            'real_name':real_name,
            'id_card':id_card
        };
        // 信息填写不完整
        if(!real_name || !id_card){
            $('.error-msg').show();
            return;
        }
        $.ajax({
                url:'/api/v1.0/users/auth',
                type:'post',
                data:JSON.stringify(params),
                contentType:'application/json',
                headers:{'X-CSRFToken':getCookie('csrf_token')},
                success:function(response){
                    if(response.errno=='0'){
                        // 成功, 信息不能修改,保存按钮隐藏
                        showSuccessMsg();
                        $('#real-name').attr('disabled','disabled');
                        $('#id-card').attr('disabled','disabled');
                        $('.btn-success').hide();
                    }else if(response.errno=='4101'){
                        location.href='/'
                    }else {
                        alert(response.errmsg)
                    }
                }
            });
    });

});