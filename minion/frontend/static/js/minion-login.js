// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

$(document).ready(function() {

    navigator.id.logout();

    navigator.id.watch({
        loggedInUser: null,
	onlogin: function(assertion) {
	    $.ajax({
		type: 'POST',
		url: '/persona/login',
		data: {assertion: assertion},
		success: function(res, status, xhr) {
		    if (res.success) {
			window.location.replace("/");
		    } else {
                        navigator.id.logout();
                    }
		},
		error: function(xhr, status, err) {
		    navigator.id.logout();
		    alert("Login failure: " + err);
		}
	    });
	},
	onlogout: function() {
	    // TODO Not sure what to do here or why this would be called from a login page
	}
    });

    var signinLink = document.getElementById('signin');
    if (signinLink) {
	signinLink.onclick = function() { navigator.id.request(); };
    }
});
