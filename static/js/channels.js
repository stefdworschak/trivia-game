let channel_closed_unexpectedly = 0;

function ChannelActions(data, options){
    this.trivia = setTriviaActions(data, options);
    this.cah = setCahActions(data, options);
}

function setChannels(options){
    const partySocket = new WebSocket(options.connection_uri);

    partySocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        ChannelActions.call('trivia', data, options);
    };

    partySocket.onclose = function(e) {
        console.error('Web socket closed unexpectedly');
        if(channel_closed_unexpectedly < 6){
            setChannels(options);
            channel_closed_unexpectedly++;
            console.log("Number of times occurred: "+ channel_closed_unexpectedly);
        }
    };

    partySocket.onopen = function(e) {
        console.log('Web socket opened successfully.');
    };
    return partySocket;
}

function setTriviaActions(data, options){
    console.log(data)
    console.log("SOURCE")
    console.log(options.source)
    switch(options.source){
        case 'start_screen':
            if(data.message == 'game_starts'){
                const timer_options = {
                    "selector": ".party-starting",
                    "party_type": options.party_type,
                    "party_name": options.party_name,
                    "seconds": 10
                }
                start_timer(timer_options);
            }
            if(data.player_name != null && data.player_name != undefined) {
                appendPlayerIfNotExists(data.player_name, '.players-list');
            }
        case 'waiting_screen':
            if(options.party_type == 'cah') {
                if(data.message == 'white_cards_complete'){
                    setTimeout(function(){
                        window.location.replace(`/${options.party_type}/${options.party_name}/choose`);
                    }, 2000)
                }
            } else if(options.party_type == 'trivia') {
                if(data.message == 'round_complete'){
                    if(data.submission_score != undefined && data.submission_score != null){
                        try{
                            const submission_score = JSON.parse(data.submission_score);
                            const submission_options = {
                                "submission": submission_score.submissions[player_name],
                                "correct_answer": submission_score.correct_answer,
                                "party_type": party_type,
                                "party_name": party_name
                            }
                            console.log("submission_options")
                            console.log(submission_options)
                            processSubmission(submission_options);
                        } catch(e){
                            console.log(e)
                            setTimeout(function(){
                                window.location.replace(`/${options.party_type}/${options.party_name}`);
                            }, 2000)
                        }
                        
                    }
                }
            }
        case 'choose_screen':
            if(data.message == 'enable-id' && options.player_name != data.player_name){
                $(`#${data.submission_score}`).removeClass('disabled');
                $(`#${data.submission_score}`).tab('show');
            } else if(data.message == 'replace-text' && options.player_name != data.player_name){
                let replace_data = JSON.parse(data.submission_score);
                $(replace_data.id).html(replace_data.text);
            } else if(data.message == 'white_cards_complete'){
                window.location.replace(`/${options.party_type}/${options.party_name}/party`);
            } else if(data.message == 'cah_round_complete'){
                $('#waiting').hide();
                $('#choose_screen').hide();
                console.log(options.player_name);
                console.log(data.player_name);
                console.log(options.player_name == data.player_name)
                if(data.submission_score == options.player_name) {
                    $('#correct').show();
                } else if(options.player_name == data.player_name){
                    $('#owner').show();
                } else {
                    $('#wrong').show();
                }
                const timer_options = {
                    "selector": ".party-starting",
                    "party_type": options.party_type,
                    "party_name": options.party_name,
                    "seconds": 3
                }
                start_timer(timer_options);
            }
        case 'finish_screen':
            if(data.message == 'party_recreated'){
                let new_party_name = "";
                $('#play-again').text("Playing again").attr('disabled', true);
                new_party_name = data.submission_score;
                window.location.replace(`/start/${new_party_name}`);
            }
        default:
            if(data.message == 'game_starts'){
                const timer_options = {
                    "selector": ".party-starting",
                    "party_type": options.party_type,
                    "party_name": options.party_name,
                    "seconds": 10
                }
                start_timer(timer_options);
            }
            if(data.player_name != null && data.player_name != undefined) {
                appendPlayerIfNotExists(data.player_name, '.players-list');
            }
    }
}

function setCahActions(data, options){

}

