function create_invite_link(selector){
    /* Creates and copies the join link */
    $(selector).click(function(){
        const element = document.createElement('input');
        const url = window.location.href;
        element.value = url.replace('/trivia/','/join/').replace('/waiting/','/join/').replace('/start/','/join/');
        document.body.appendChild(element);
        element.select();
        document.execCommand('copy');
        document.body.removeChild(element);
        const options = {
            'title': 'Link copied',
            'placement': 'auto'
        }
        let tooltip_target = $(this);
        tooltip_target.tooltip(options);
        tooltip_target.tooltip('show');
        setTimeout(function(){
            tooltip_target.tooltip('dispose');
        },1000)
        
    })
}

function start_timer(options){
    /* Runs a timer and redirects the player to the main game once finished */
    $(options.selector).text(`Starting in ${options.seconds}s`)
    if(options.seconds > 0){
        options.seconds--; 
        setTimeout(function(){
            start_timer(options);
        }, 1000);
    } else {
        window.location.replace(`/${options.party_type}/${options.party_name}`);
    }
}

function appendPlayerIfNotExists(player_name, selector){
    /* Appends player name to the list of player names given a selector */
    const matches = $(`${selector} li:contains(${player_name})`).length;
    if(matches == 0){
        let ul = $(`${selector} ul`)
        let li = $('<li></li>');
        let span = $('<span class="badge badge-pill badge-dark username"></span>');
        span.text(player_name);
        li.append(span);
        ul.append(li);
    }
}

function processSubmission(options){
    if(options.submission == 1){
        // Correct
        $('#waiting').hide();
        $('#correct').show();
        setTimeout(function(){
            window.location.replace(`/${options.party_type}/${options.party_name}`);
        }, 2000)
    } else if (options.submission == 0) {
        // Incorrect
        $('#waiting').hide();
        $('#correct-answer').html(options.correct_answer)
        $('#wrong').show();
        setTimeout(function(){
            window.location.replace(`/${options.party_type}/${options.party_name}`);
        }, 2000)
    }
}