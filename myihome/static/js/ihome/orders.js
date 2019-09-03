//模态框居中的控制
function centerModals(){
    $('.modal').each(function(i){   //遍历每一个模态框
        var $clone = $(this).clone().css('display', 'block').appendTo('body');    
        var top = Math.round(($clone.height() - $clone.find('.modal-content').height()) / 2);
        top = top > 0 ? top : 0;
        $clone.remove();
        $(this).find('.modal-content').css("margin-top", top-30);  //修正原先已经有的30个像素
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function(){
    $('.modal').on('show.bs.modal', centerModals);      //当模态框出现的时候
    $(window).on('resize', centerModals);

    var queryData = decodeQuery();
    var role = queryData["role"];
    // 查询房客订单
    $.get('/api/v1.0/user/orders?role='+role,function (res) {
        if(res.errno=='0'){
            render_template=template('orders-list-tmpl',{'orders':res.data.orders});
            $('.orders-list').html(render_template);
            //  查询成功之后需要设置评论的相关处理
            $(".order-pay").on("click", function (){
                var orderId = $(this).parents("li").attr("order-id");
                $.ajax({
                    url:"/api/v1.0/orders/" + orderId + "/payment",
                    type:"post",
                    dataType:"json",
                    headers:{
                        "X-CSRFToken":getCookie("csrf_token"),
                    },
                    success:function (resp) {
                        if("4101" == resp.errno) {
                            location.href = "/login.html";
                        }else if ("0" == resp.errno){
                            // lead user to pay_url
                            location.href = resp.data.pay_url;
                        }
                    }
                });
            });
            $(".order-comment").on("click", function () {
                var orderId = $(this).parents("li").attr("order-id");
                // setting OrderId
                //点击评论之后，将获取到的orderId设置到弹窗的确认按钮，以便向后传值
                $(".modal-comment").attr("order-id",orderId)
            });
            $(".modal-comment").on("click", function () {
                var orderId = $(this).attr("order-id");
                var comment = $("#comment").val();
                if(!comment) return;
                var data = {
                    order_id:orderId,
                    comment:comment
                };
                // process comment
                $.ajax({
                    url: "/api/v1.0/orders/" + orderId + "/comment",
                    type:"PUT",
                    data:JSON.stringify(data),
                    contentType:"application/json",
                    dataType: "json",
                    headers: {
                        "X-CSRFToken":getCookie("csrf_token")
                    },
                    success: function (resp) {
                        if ("4101" == resp.errno){
                            location.href = "/login.html"
                        }else if("0" == resp.errno){
                            // 成功评论之后设置订单状态为已完成
                            $(".orders-list>li[order-id="+ orderId +"]>div.order-content>div.order-text>ul li:eq(4)>span").html("已完成");
                            // 隐藏发表评论按钮
                            $("ul.orders-list>li[order-id="+ orderId +"]>div.order-title>div.order-operate").hide();
                            // 最后将发表评论弹框隐藏
                            $("#comment-modal").modal("hide");
                        }
                    }
                })
            })
        } else if(res.errno=='4101'){
            location.href='/login.html'
        }else {
            alert(res.errmsg)
        }
    },"json");

});
