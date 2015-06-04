function delete_entry() {
	$.post(Flask.url_for('delete_def'), { definition_id: defid }, function(data) {
		window.location.replace(Flask.url_for('index'));
		console.log('It didn\'t redirect');
	});
}
