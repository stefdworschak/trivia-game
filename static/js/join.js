$(document).ready(function(){

    $('#find_player').click(function(){
        const player_name = $('#player_name').val();
        $.ajax({
            'url':'/join/find_player',
            'method': 'POST',
            'data': {'player_name': player_name},
            'success': function(res){
                console.log(res)
                if(res.player_exists == false){
                    $('.error_output').show();
                    $('#reset_join_player').hide();
                    $('.error_output').text('Player not found. Please create a new player.')
                } else {
                    $('input[name="player"]').val(player_name);
                    $('.error_output').hide();
                    $('#reset_join_player').show();
                    $('#player_name').prop('disabled', true);
                    $('#join_party').prop('disabled', false);
                    $('#find_player').prop('disabled', true);
                    $('#create_player').prop('disabled', true);
                }
            }
        })
    })

    $('#create_player').click(function(){
        const player_name = $('#player_name').val();
        $.ajax({
            'url':'/join/create_player',
            'method': 'POST',
            'data': {'player_name': player_name},
            'success': function(res){
                console.log(res)
                if(res.player_exists == false){
                    $('.error_output').show();
                    $('#reset_join_player').hide();
                    $('.error_output').text('Player could not be created.')
                } else {
                    $('input[name="player"]').val(player_name);
                    $('.error_output').hide();
                    $('#reset_join_player').show();
                    $('#player_name').prop('disabled', true);
                    $('#join_party').prop('disabled', false);
                    $('#find_player').prop('disabled', true);
                    $('#create_player').prop('disabled', true);

                }
            }
        })
    })

    $('#reset_join_player').click(function(){
        $('.error_output').hide();
        $('#reset_join_player').hide();
        $('#player_name').prop('disabled', false).val('');
        $('#join_party').prop('disabled', true);
        $('#find_player').prop('disabled', false);
        $('#create_player').prop('disabled', false)
        $('input[name="player"]').val('')
    })

    $('#join_form').submit(function(event){
        if($('#player_name').val() == '' || $('#player_name').prop('disabled') == false){
            console.log(true)
            event.preventDefault();
        }
    })

})