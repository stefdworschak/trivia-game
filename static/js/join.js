$(document).ready(function(){

    $('#name_modal').modal({
        backdrop: 'static',
        keyboard: false
      });
    
    $('#find_player').click(function(){
        const player_name = $('#player_name').val();
        $.ajax({
            'url':'/party/join/find_player',
            'method': 'POST',
            'data': {'player_name': player_name},
            'success': function(res){
                console.log(res)
            }
        })
    })

})