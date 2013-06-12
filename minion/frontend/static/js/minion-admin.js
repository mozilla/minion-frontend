// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

// Controllers for /users

app.controller("AdminUsersController", function($scope, $routeParams, $http, $location) {
    $scope.$on('$viewContentLoaded', function() {
        $http.get('/api/admin/users')
            .success(function(response, status, headers, config) {
                $scope.users = response.data;
            });
    });
});

// Controllers for /groups

app.controller("AdminAddGroupController", function ($scope, dialog, group) {
    $scope.group = group;
    $scope.close = function(result){
        dialog.close(group);
    };
});

app.controller("AdminGroupsController", function($scope, $routeParams, $http, $location, $dialog) {
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
            templateUrl: "static/partials/admin/add-group-dialog.html",
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

app.controller("AdminAddUserController", function ($scope, dialog) {
    $scope.close = function(site){
        dialog.close(site);
    };
});

app.controller("AdminAddSiteController", function ($scope, dialog) {
    $scope.close = function(site){
        dialog.close(site);
    };
});

app.controller("AdminGroupController", function($scope, $routeParams, $http, $location, $dialog) {
    var reload = function () {
        $http.get('/api/admin/groups/' + $routeParams.groupName)
            .success(function(response, status, headers, config) {
                $scope.group = response.data;
            });
    };

    $scope.addUser = function() {
        $dialog.dialog({templateUrl: "static/partials/admin/add-user-dialog.html?x=1", controller: "AdminAddUserController" })
            .open().then(function(email) {
                if (email) {
                    var patch = {addUsers:[email]};
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

    $scope.removeUser = function(email) {
        var title = 'Delete User';
        var msg = 'Are you sure you want to remove ' + email + ' from the group?';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $dialog.messageBox(title, msg, btns).open().then(function(result){
            if (result) {
                var patch = {removeUsers:[email]};
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

    $scope.addSite = function() {
        console.log("ADD SITE");
        $dialog.dialog({templateUrl: "static/partials/admin/add-site-dialog.html?x=1", controller: "AdminAddSiteController" })
            .open().then(function(url) {
                if (url) {
                    var patch = {addSites:[url]};
                    var api = '/api/admin/groups/' + $routeParams.groupName;
                    $http({method:'PATCH', url:api, headers: {"Content-Type": "application/json"}, data:patch})
                        .success(function(response, status, headers, config) {
                            if (response.success) {
                                reload();
                            }
                        });
                }
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

// Controllers for /admin/sites

app.controller("AdminCreateSiteController", function ($scope, dialog, plans) {
    $scope.site = {url:"",plans:[]};
    $scope.plans = plans;
    $scope.close = function(site){
        dialog.close(site);
    };
});

app.controller("AdminSitesController", function($scope, $routeParams, $http, $dialog) {
    var reload = function() {
        $http.get('/api/admin/sites')
            .success(function(response, status, headers, config) {
                $scope.sites = response.data;
            });
    };

    $scope.createSite = function () {

        $http.get('/api/admin/plans')
            .success(function(response, status, headers, config) {
                var d = $dialog.dialog({
                    templateUrl: "static/partials/admin/sites/create-site.html?x=" + new Date().getTime(),
                    controller: "AdminCreateSiteController",
                    resolve: { plans: function() { return response.data; } }
                });
                d.open().then(function(site) {
                    if(site) {
                        $http.post('/api/admin/sites', {url: site.url, plans: site.plans})
                            .success(function(response, status, headers, config) {
                                if (response.success) {
                                    reload();
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
