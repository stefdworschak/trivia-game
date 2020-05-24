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
    };

    partySocket.onopen = function(e) {
        console.log('Web socket opened successfully.');
    };
}

function setTriviaActions(data, options){
    console.log(data)
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
                        processSubmission(submission_options);
                    } catch(e){
                        console.log(e)
                        setTimeout(function(){
                            window.location.replace(`/${options.party_type}/${options.party_name}`);
                        }, 2000)
                    }
                    
                }
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

