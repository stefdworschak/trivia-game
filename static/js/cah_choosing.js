function enableChoosing(num_submissions, num_picks, socket, player_name, party_name){
    let revealed = 0;
    $('.reveal-pick').click(function(){
        let player = $(this).data('player');
        let card_text = $(this).data('text');
        let black_card = $(`#black_card_${player} div`);
        let replace_text = "";
        if(black_card.text().indexOf('______') > -1){
            replace_text = black_card.text().replace('______','<b>'+card_text+'</b>');
        } else {
            replace_text = black_card.text() + ' <b>' + card_text + '</b>';
        }
        black_card.html(replace_text);
        let data = {"type":"navigation", 
                "submission_score": JSON.stringify({"text": replace_text, "id": `#black_card_${player} div`}), 
                "message": "replace-text",
                "player_name": player_name};
        socket.send(JSON.stringify(data));
        $(this).attr('disabled', true);
        revealed++;
        let reveal_options = {
            'party_name': party_name,
            'type': 'card',
            'player_name': $(this).data('player'),
            'card_id': $(this).data('card-id')
        }
        markRevealed(reveal_options);
        if(revealed == (num_submissions * num_picks)) {
            $('.submit-winner').attr('disabled', false);
            $('.nav-item.nav-link').off();
            $('.reveal-section').off();
        }
    })
}

function handleNavigation(socket, player_name){
    $('.nav-item.nav-link').click(function(){
        let id = $(this).attr('id');
        let data = {"type":"navigation", 
                "submission_score": id, 
                "message": "enable-id",
                "player_name": player_name};
        socket.send(JSON.stringify(data));
    })
}

function enableNavReveal(party_name){
    $('.reveal-section').click(function(){
        let reveal_options = {
            'party_name': party_name,
            'type': 'submission',
            'player_name': $(this).data('player'),
            'card_id': $(this).data('card-id')
        }
        markRevealed(reveal_options);
    })
}

function markRevealed(options){
    console.log(options)
    $.post(`/cah/${options.party_name}/mark_revealed`, options)
        .then(function(res){
        console.log(res)
    })
}

function revealCardText(card_text, player){
    let black_card = $(`#black_card_${player} div`);
    console.log(black_card);
    console.log(card_text)
    let replace_text = "";
    if(black_card.text().indexOf('______') > -1){
        replace_text = black_card.text().replace('______','<b>'+card_text+'</b>');
    } else {
        replace_text = black_card.text() + ' <b>' + card_text + '</b>';
    }
    black_card.html(replace_text);
}

function revealAll(submissions) {
    console.log("Revealing")
    console.log(submissions)
    let latest_section = null;
    for (var s in submissions){
        let sub = submissions[s];
        if(sub.revealed){
            latest_section = `#nav-p${parseInt(s)+1}-tab`;
        } 
        for (var c in sub.white_cards){
            let card = sub.white_cards[c];
            if(card.revealed){
                revealCardText(card.card_text, sub.player);
            }
        }
    }
    $(latest_section).tab('show');
}