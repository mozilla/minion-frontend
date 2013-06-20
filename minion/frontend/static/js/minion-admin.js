// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

// Controllers for /users

app.controller("AdminCreateUserController", function ($scope, dialog, users, groups) {
    $scope.user = {email:"", name: "", groups:[], role: "user"};
    $scope.groups = groups;
    $scope.roles = ["user", "administrator"];

    $scope.cancel = function () {
        dialog.close(null);
    };

    $scope.submit = function(user) {
        if (_.find(users, function (u) { return u.email === user.email })) {
            $scope.error = "The user already exists.";
        } else {
            dialog.close(user);
        }
    };
});

app.controller("AdminUsersController", function($scope, $http, $dialog) {
    var reload = function() {
        $http.get('/api/admin/users')
            .success(function(response, status, headers, config) {
                $scope.users = response.data;
            });
    };

    $scope.removeUser = function(user) {
        var title = 'Remove User';
        var msg = 'Are you sure you want to remove ' + user.email + ' from minion?';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $dialog.messageBox(title, msg, btns).open().then(function(result) {
            if (result) {
                $http.delete('/api/admin/users/' + user.email).success(function(response, status, headers, config) {
                    reload();
                });
            }
        });
    };

    $scope.createUser = function () {
        $http.get('/api/admin/groups')
            .success(function(response, status, headers, config) {
                var d = $dialog.dialog({
                    templateUrl: "static/partials/admin/users/create-user.html?x=" + new Date().getTime(),
                    controller: "AdminCreateUserController",
                    resolve: { users: function() { return $scope.users; },
                               groups: function() { return response.data; } }
                });
                d.open().then(function(user) {
                    if(user) {
                        console.dir(user);
                        $http.post('/api/admin/users', {email:user.email, name: user.name, role: user.role, groups: user.groups})
                            .success(function(response, status, headers, config) {
                                if (response.success) {
                                    reload();
                                } else {
                                    // TODO Show an error dialog
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

app.controller("AdminAddUserController", function ($scope, dialog, users) {
    $scope.users = users;
    $scope.cancel = function() {
        dialog.close(null);
    };
    $scope.submit = function(email){
        dialog.close(email);
    };
});

app.controller("AdminAddSiteController", function ($scope, dialog, sites) {
    $scope.sites = sites;
    $scope.submit = function(site){
        dialog.close(site);
    };
    $scope.cancel = function(site){
        dialog.close(null);
    };
});

app.controller("AdminGroupController", function($scope, $routeParams, $http, $location, $dialog) {
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

// Controllers for /admin/sites

app.controller("AdminEditSiteController", function ($scope, dialog, site, plans) {
    $scope.site = site;
    $scope.plans = plans;

    $scope.cancel = function () {
        dialog.close(null);
    };

    $scope.submit = function(site) {
        dialog.close(site);
    };
});

app.controller("AdminCreateSiteController", function ($scope, dialog, plans, sites) {
    $scope.site = {url:"",plans:[]};
    $scope.plans = plans;

    $scope.cancel = function () {
        dialog.close(null);
    };

    $scope.submit = function(site) {
        if (_.find(sites, function (s) { return s.url === site.url; })) {
            $scope.error = "The site already exists.";
        } else {
            dialog.close(site);
        }
    };
});

app.controller("AdminSitesController", function($scope, $routeParams, $http, $dialog) {
    var reload = function() {
        $http.get('/api/admin/sites')
            .success(function(response, status, headers, config) {
                $scope.sites = response.data;
            });
    };

    $scope.editSite = function (site) {
        console.dir(site);
        $http.get('/api/admin/plans').success(function(response) {
            $scope.plans = response.data;
                var d = $dialog.dialog({
                    templateUrl: "static/partials/admin/sites/edit-site.html?x=" + new Date().getTime(),
                    controller: "AdminEditSiteController",
                    resolve: { plans: function() { return $scope.plans; },
                               site: function() { return angular.copy(site); } }
                });
                d.open().then(function(site) {
                    if (site) {
                        console.dir(site);
                        $http.post('/api/admin/sites/' + site.id, {plans: site.plans}).success(function(response) {
                            reload();
                        });
                    }
                });
        });
    };

    $scope.createSite = function () {

        $http.get('/api/admin/plans').success(function(response) {
            $scope.plans = response.data;
            $http.get('/api/admin/sites').success(function(response) {
                $scope.sites = response.data;
                var d = $dialog.dialog({
                    templateUrl: "static/partials/admin/sites/create-site.html?x=" + new Date().getTime(),
                    controller: "AdminCreateSiteController",
                    resolve: { plans: function() { return $scope.plans; },
                               sites: function() { return $scope.sites; } }
                });
                d.open().then(function(site) {
                    if(site) {
                        $http.post('/api/admin/sites', {url: site.url, plans: site.plans}).success(function(response) {
                            if (response.success) {
                                reload();
                            }
                        });
                    }
                });
            });
        });
    };

    $scope.$on('$viewContentLoaded', function() {
        reload();
    });
});
