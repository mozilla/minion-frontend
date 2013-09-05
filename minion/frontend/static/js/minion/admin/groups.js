// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

var minionAdminGroupsModule = angular.module('minionAdminGroupsModule', []);


// Controllers for /groups

minionAdminGroupsModule.controller("AdminAddGroupController", function ($scope, dialog, group) {
    $scope.group = group;
    $scope.close = function(result){
        dialog.close(group);
    };
});

minionAdminGroupsModule.controller("AdminGroupsController", function($scope, $routeParams, $http, $location, $dialog) {

    $scope.navItems = app.navContext('admin');

    var reload = function () {
        $http.get('/api/admin/groups')
            .success(function(response, status, headers, config) {
                $scope.groups = response.data;
            });
    };

    $scope.removeGroup = function(groupName) {
        var title = 'Delete Group';
        var msg = 'Are you sure you want to delete the ' + groupName + ' group? This will not delete any sites or users but will delete the association between them.';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $dialog.messageBox(title, msg, btns).open().then(function(result){
            if (result) {
                $http.delete('/api/admin/groups/' + groupName)
                    .success(function(response, status, headers, config) {
                        if (response.success) {
                            reload();
                        }
                    });
            }
        });
    };

    $scope.addGroup = function(){
        var group = {name:"", description:""};
        var d = $dialog.dialog({
            templateUrl: "static/partials/admin/add-group-dialog.html?" + new Date().getTime(),
            controller: "AdminAddGroupController",
            resolve: {
                group: function () {
                    return angular.copy(group)
                }
            }
        });
        d.open().then(function(group) {
            if(group) {
                $http.post('/api/admin/groups', group)
                    .success(function(response, status, headers, config) {
                        if (response.success) {
                            reload();
                        }
                    });
            }
        });
    };

    $scope.$on('$viewContentLoaded', function() {
        reload();
    });
});

// Controllers for /groups/:groupName

minionAdminGroupsModule.controller("AdminAddUserController", function ($scope, dialog, users) {
    $scope.users = users;
    $scope.cancel = function() {
        dialog.close(null);
    };
    $scope.submit = function(email){
        dialog.close(email);
    };
});

minionAdminGroupsModule.controller("AdminAddSiteController", function ($scope, dialog, sites) {
    $scope.sites = sites;
    $scope.submit = function(site){
        dialog.close(site);
    };
    $scope.cancel = function(site){
        dialog.close(null);
    };
});

minionAdminGroupsModule.controller("AdminGroupController", function($scope, $routeParams, $http, $location, $dialog) {

    $scope.navItems = app.navContext('admin');

    // TODO: This is incredibly hackish outside of what exists. We may
    // need a better pattern for sub navigation.
    var groupRoute = _.first(app.navContext('admin:groups'));
    groupRoute.href = groupRoute.href.replace(
                        /:groupName/, $routeParams.groupName);

    // Insert the group nav item after the Groups parent nav.
    var insertAt = _.indexOf(_.pluck($scope.navItems, 'slug'), 'groups') + 1;
    $scope.navItems.splice(insertAt, 0, groupRoute);

    var reload = function () {
        $http.get('/api/admin/groups/' + $routeParams.groupName).success(function(response) {
            $scope.group = response.data;
        });
    };

    $scope.addUser = function() {
        $http.get("/api/admin/users").success(function(response) {
            // Remove the sites already in the group. Sort them.
            var users = _.filter(response.data, function (user) { return !_.contains($scope.group.users, user.email); });
            // Show the dialog
            var r = { users: function () { return users; } };
            $dialog.dialog({templateUrl: "static/partials/admin/add-user-dialog.html?" + new Date().getTime(), controller: "AdminAddUserController", resolve: r }).open().then(function(user) {
                if (user) {
                    var patch = {addUsers:[user.email]};
                    var url = '/api/admin/groups/' + $routeParams.groupName;
                    $http({method:'PATCH', url:url, headers: {"Content-Type": "application/json"}, data:patch}).success(function(response) {
                        reload();
                    });
                }
            });
        });
    };

    $scope.removeUser = function(email) {
        var title = 'Delete User';
        var msg = 'Are you sure you want to remove ' + email + ' from the group?';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $dialog.messageBox(title, msg, btns).open().then(function(result) {
            if (result) {
                var patch = {removeUsers:[email]};
                var url = '/api/admin/groups/' + $routeParams.groupName;
                $http({method:'PATCH', url:url, headers: {"Content-Type": "application/json"}, data:patch}).success(function(response) {
                        reload();
                });
            }
        });
    };

    $scope.addSite = function() {
        $http.get("/api/admin/sites").success(function(response) {
            // Remove the sites already in the group. Sort them.
            var sites = _.filter(response.data, function (site) { return !_.contains($scope.group.sites, site.url); });
            // Show the dialog
            var r = { sites: function () { return sites; } };
            $dialog.dialog({templateUrl: "static/partials/admin/add-site-dialog.html?" + new Date().getTime(), controller: "AdminAddSiteController", resolve: r }).open().then(function(site) {
                if (site) {
                    var patch = {addSites:[site.url]};
                    var url = '/api/admin/groups/' + $routeParams.groupName;
                    $http({method:'PATCH', url:url, headers: {"Content-Type": "application/json"}, data:patch}).success(function(response) {
                        reload();
                    });
                }
            });
        });
    };

    $scope.removeSite = function(site) {
        var title = 'Remove Site';
        var msg = 'Are you sure you want to remove ' + site + ' from the group?';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $dialog.messageBox(title, msg, btns).open().then(function(result){
            if (result) {
                var patch = {removeSites:[site]};
                var url = '/api/admin/groups/' + $routeParams.groupName;
                $http({method:'PATCH', url:url, headers: {"Content-Type": "application/json"}, data:patch})
                    .success(function(response, status, headers, config) {
                        if (response.success) {
                            reload();
                        }
                    });
            }
        });
    };

    $scope.$on('$viewContentLoaded', function() {
        reload();
    });
});
