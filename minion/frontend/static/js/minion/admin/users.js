// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.


var minionAdminUsersModule = angular.module('minionAdminUsersModule', []);


minionAdminUsersModule.controller("AdminEditUserController", function ($scope, modal, user, groups) {
    $scope.user = user;
    $scope.groups = groups;
    $scope.roles = ["user", "administrator"];

    $scope.cancel = function () {
        modal.close(null);
    };

    $scope.submit = function() {
        modal.close($scope.user);
    };
});


minionAdminUsersModule.controller("AdminCreateUserController", function ($scope, modal, users, groups) {
    $scope.user = {email:"", name: "", groups:[], role: "user"};
    $scope.groups = groups;
    $scope.roles = ["user", "administrator"];

    $scope.cancel = function () {
        modal.close(null);
    };

    $scope.submit = function(user) {
        if (_.find(users, function (u) { return u.email === user.email; })) {
            $scope.error = "The user already exists.";
        } else {
            modal.close(user);
        }
    };
});


minionAdminUsersModule.controller("AdminUsersController", function($scope, $http, $modal) {
    $scope.navItems = app.navContext('admin');

    var reload = function() {
        $http.get('/api/admin/users')
            .success(function(response, status, headers, config) {
                $scope.users = response.data;
            });
    };

    $scope.editUser = function (user) {
        $http.get('/api/admin/groups').success(function(response) {
            $scope.groups = response.data;
                var d = $modal.modal({
                    templateUrl: "static/partials/admin/users/edit-user.html",
                    controller: "AdminEditUserController",
                    resolve: { groups: function() { return $scope.groups; },
                               user: function() { return angular.copy(user); } }
                });
                d.open().then(function(user) {
                    if (user) {
                        $http.post('/api/admin/users/' + user.email, user).success(function(response) {
                            reload();
                        });
                    }
                });
        });
    };

    $scope.removeUser = function(user) {
        var title = 'Remove User';
        var msg = 'Are you sure you want to remove ' + user.email + ' from minion?';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $modal.messageBox(title, msg, btns).open().then(function(result) {
            if (result) {
                $http.delete('/api/admin/users/' + user.email).success(function() {
                    reload();
                });
            }
        });
    };

    $scope.createUser = function () {
        $http.get('/api/admin/groups').success(function(response) {
            var d = $modal.modal({
                templateUrl: "static/partials/admin/users/create-user.html",
                controller: "AdminCreateUserController",
                resolve: { users: function() { return $scope.users; },
                           groups: function() { return response.data; } }
            });
            d.open().then(function(user) {
                if(user) {
                    data = {email: user.email, name: user.name, role: user.role, groups: user.groups};
                    $http.post('/api/admin/users', data).success(function(response) {
                        if (response.success) {
                            reload();
                        } else {
                            // TODO Show an error modal
                        }
                    });
                }
            });
        });
    };

    $scope.$on('$viewContentLoaded', function() {
        reload();
    });
});
