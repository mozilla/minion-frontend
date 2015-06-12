// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.


var minionAdminGroupsModule = angular.module('minionAdminGroupsModule', []);


minionAdminGroupsModule.controller("AdminAddGroupController", function ($scope, $modalInstance, group) {
    $scope.group = group;
    $scope.close = function(result){
        $modalInstance.close(group);
    };
});


minionAdminGroupsModule.controller("AdminGroupsController", function($scope, $routeParams, $http, $location, $modal, $dialog) {

    $scope.navItems = app.navContext('admin');

    var reload = function () {
        $http.get('/api/admin/groups').success(function(response) {
            $scope.groups = response.data;
        });
    };

    $scope.removeGroup = function(groupName) {
        var title = 'Delete Group';
        var msg = 'Are you sure you want to delete the ' + groupName
                + ' group? This will not delete any sites or users but will delete the association between them.';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $dialog.messageBox(title, msg, btns).open().then(function(result){
            if (result) {
                $http.delete('/api/admin/groups/' + groupName).success(function(response) {
                    if (response.success) {
                        reload();
                    }
                });
            }
        });
    };

    $scope.addGroup = function(){
        var group = {name:"", description:""};
        var d = $modal.open({
            templateUrl: "static/partials/admin/add-group-dialog.html",
            controller: "AdminAddGroupController",
            resolve: {
                group: function () {
                    return angular.copy(group);
                }
            }
        });
        d.result.then(function(group) {
            if(group) {
                $http.post('/api/admin/groups', group).success(function(response) {
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


minionAdminGroupsModule.controller("AdminAddUserController", function ($scope, $modalInstance, users) {
    $scope.users = users;
    $scope.cancel = function() {
        $modalInstance.close(null);
    };
    $scope.submit = function(email){
        $modalInstance.close(email);
    };
});


minionAdminGroupsModule.controller("AdminAddSiteController", function ($scope, $modalInstance, sites) {
    $scope.sites = sites;
    $scope.submit = function(site){
        $modalInstance.close(site);
    };
    $scope.cancel = function(site){
        $modalInstance.close(null);
    };
});


minionAdminGroupsModule.controller("AdminGroupController", function($scope, $routeParams, $http, $location, $modal, $dialog) {

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
            var users = _.filter(response.data, function (user) {
                return !_.contains($scope.group.users, user.email);
            });
            // Show the dialog
            var r = { users: function () { return users; } };
            var d = $modal.open({templateUrl: "static/partials/admin/add-user-dialog.html",
                                    controller: "AdminAddUserController", resolve: r });
            d.result.then(function(user) {
                if (user) {
                    var patch = {addUsers:[user.email]};
                    var url = '/api/admin/groups/' + $routeParams.groupName;
                    var headers = {"Content-Type": "application/json"};
                    $http({method: 'PATCH', url: url, headers: headers, data: patch}).success(function(response) {
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
                var headers = {"Content-Type": "application/json"};
                $http({method: 'PATCH', url: url, headers: headers, data: patch}).success(function(response) {
                        reload();
                });
            }
        });
    };

    $scope.addSite = function() {
        $http.get("/api/admin/sites").success(function(response) {
            // Remove the sites already in the group. Sort them.
            var sites = _.filter(response.data, function (site) {
                return !_.contains($scope.group.sites, site.url);
            });
            // Show the modal
            var r = { sites: function () { return sites; } };
            var d = $modal.open({templateUrl: "static/partials/admin/add-site-dialog.html",
                                    controller: "AdminAddSiteController", resolve: r });
            d.result.then(function(site) {
                if (site) {
                    var patch = {addSites:[site.url]};
                    var url = '/api/admin/groups/' + $routeParams.groupName;
                    var headers = {"Content-Type": "application/json"};
                    $http({method: 'PATCH', url: url, headers: headers, data: patch}).success(function(response) {
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
                var headers = {"Content-Type": "application/json"};
                $http({method: 'PATCH', url: url, headers: headers, data: patch}).success(function(response) {
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
