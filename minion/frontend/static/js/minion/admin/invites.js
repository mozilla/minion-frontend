// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.


var minionAdminInvitesModule = angular.module('minionAdminInvitesModule', []);


minionAdminInvitesModule.controller("AdminCreateInviteController", function($scope, $modalInstance, users, groups) {
    $scope.invite = {recipient: ""};
    $scope.groups = groups;
    $scope.roles = ["user", "administrator"];
    $scope.opts = {
        'accept': true,
        'decline': true
    };
    $scope.navItems = app.navContext('admin');

    // todo: do cleanup!
    $scope.cancel = function() {
        $modalInstance.close(null);
    };

    $scope.submit = function(result) {
        result.opts = $scope.opts;
        $modalInstance.close(result);
    };
});


minionAdminInvitesModule.controller("AdminInvitesController", function($scope, $http, $modal, $filter, $location) {
    $scope.navItems = app.navContext('admin');

    var base_url = $location.absUrl().split("#!")[0] + '#!/invite';
    var reload = function() {
        $http.get('/api/admin/invites').success(function(response) {
            $scope.invites = $filter('orderBy')(response.data, 'sent_on');
        });
    };

    $scope.createInvite = function () {
        $http.get('/api/admin/groups').success(function(response) {
            var d = $modal.open({
                templateUrl: "static/partials/admin/invites/create-invites.html",
                controller: "AdminCreateInviteController",
                resolve: { users: function() { return $scope.users; },
                           groups: function() { return response.data; }}
            });

            d.result.then(function(result) {
                if(result) {
                    var data1 = {email: result.email, name: result.name, role: result.role, groups: result.groups,
                                 invitation: true};

                    $http.post('/api/admin/users', data1).success(function(response) {
                        if (response.success) {
                            // now we should be able to send an invite
                            var notify_when = [];
                            if (result.opts.accept) {
                                notify_when.push('accept');
                            }
                            if (result.opts.decline) {
                                notify_when.push('decline');
                            }
                            var data2 = {recipient: result.email, base_url: base_url, notify_when: notify_when};
                            $http.post('/api/admin/invites', data2).success(function(response) {
                                if (response.success) {
                                    reload();
                                }
                            });
                        } else {
                            // TODO Show an error modal
                        }
                    });
                }
            });
        });
    };

    $scope.resendInvite = function(id) {
        var data = {action: 'resend', base_url: base_url};
        $http.post('/api/admin/invites/' + id + '/control', data).success(function(response) {
            if (response.success) {
                reload();
            }
        });
    };

    $scope.removeInvite = function(id) {
        $http.delete('/api/admin/invites/' + id).success(function(response) {
            if (response.success) {
                reload();
            }
        });
    };

    $scope.$on('$viewContentLoaded', function() {
        reload();
    });
});
