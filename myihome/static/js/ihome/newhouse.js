function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){
    $('.popup_con').fadeIn('fast');
    //没有实名认证不能进入该页面
    $.get('/api/v1.0/users/auth',function (res) {
        if(res.errno=='0'){
            //判断是否实名认证
            if(!res.user_auth.real_name || !res.user_auth.id_card){
                location.href='/auth.html'
            }
        }else if(res.errno=='4101'){
            location.href='/login.html'
        }else {
            alert(res.errmsg)
        }
    });
    // TODO: 在页面加载完毕之后获取区域信息
    $.get('/api/v1.0/areas',function (res) {
        if(res.errno=='0'){
            // method 1, origin method:through js logic
            // var areas = res.data;
            // for(i=0; i<areas.length;i++){
            //     var area = areas[i];
            //     $("#area-id").append('<option value="'+area.aid +'">'+ area.aname + '</option>');
            // }

            // method 2: use the frontend template
            // template(template_name(areas-tmpl),data), you must accept it's return data(render_template),and set the data to html
            render_template=template('areas-tmpl',{'areas':res.data});
            $('#area-id').html(render_template);
            $('.popup_con').fadeOut('fast');
        }else {
            alert(res.errmsg);
            $('.popup_con').fadeOut('fast');
        }
    });
    // TODO: 处理房屋基本信息提交的表单数据
    $('#form-house-info').submit(function (event) {
        $('.popup_con').fadeIn('fast');
        event.preventDefault();

        // 收集form表单中需要提交的input标签,放在一个数组对象中
        var params={};
        // map 遍历对象，比如说数组对象
        // obj == {name: "title", value: "1"}
        // serializeArray().map()-->function will get all the input data
        $(this).serializeArray().map(function (obj) {
            params[obj.name]=obj.value;
        });
        // 收集房屋设施信息,listType
        var facilities=[];
        //获取所有设施被选中的复选框,1.:checkbox 2.:checked[name=facility], two type of selector, each(index, element)
        $(':checkbox:checked[name=facility]').each(function (index,ele) {
            //存到列表
            facilities[index]=ele.value;
        });
        //赋值给params,dynamic
        params['facility']=facilities;
        $.ajax({
                    url:'/api/v1.0/houses/info',
                    type:'post',
                    data:JSON.stringify(params),
                    contentType:'application/json',
                    dataType:"json",
                    headers:{'X-CSRFToken':getCookie('csrf_token')},
                    success:function(response){
                        if(response.errno=='0'){
                            // 成功
                            $('.popup_con').fadeOut('fast');
                            // hide basic form
                            $('#form-house-info').hide();
                            // show picture form
                            $('#form-house-image').show();
                            // setting the house_id of picture form
                            $('#house-id').val(response.data.house_id);
                        }else if(response.errno=='4101'){
                            // user not login
                            location.href='/login.html'
                        }else {
                            alert(response.errmsg);
                            $('.popup_con').fadeOut('fast');
                        }
                    }
                });
    });
    // TODO: 处理图片表单的数据
    $('#form-house-image').submit(function (event) {
        // 开始等待加载特效
        $('.popup_con').fadeIn('fast');
        event.preventDefault();
        // var house_id=$('#house-id').val();  // backend obtain the house_id directly
        $(this).ajaxSubmit({
            url:'/api/v1.0/houses/image',
            type:'post',
            headers:{'X-CSRFToken':getCookie('csrf_token')},
            success:function (res) {
                if(res.errno=='0'){
                    // 拼接显示房屋图片, use append() to add house picture
                    $('.house-image-cons').append('<img src="'+res.data.image_url+'" alt="房屋图片" />');
                    // 结束等待加载特效
                    $('.popup_con').fadeOut('fast');
                }else if(res.errno=='4101'){
                    location.href='/login.html'
                }else {
                    alert(res.errmsg);
                    $('.popup_con').fadeOut('fast');
                }
            }
        });
    });
});