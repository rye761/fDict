//This is the client-side code for voting on definitions. Requires jQuery.
function give_vote() {
	$.post(Flask.url_for('add_vote'), { definition_id: defid }, function(data) {
		$('#add_vote_button').addClass('none');		
		$('#revoke_vote_button').removeClass('none');
		$('#vote-text').html('Votes: ' + data.votes);
	});
}

function revoke_vote() {
	$.post(Flask.url_for('revoke_vote'), { definition_id: defid }, function(data) {
		$('#revoke_vote_button').addClass('none');
		$('#add_vote_button').removeClass('none');
		$('#vote-text').html('Votes: ' + data.votes);
	});
}
