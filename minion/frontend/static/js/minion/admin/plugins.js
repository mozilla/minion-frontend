// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

var minionAdminPluginsModule = angular.module('minionAdminPluginsModule', []);

minionAdminPluginsModule.controller("AdminPluginsController", function($scope, $routeParams, $http) {

    $scope.navItems = app.navContext('admin');

    var reload = function() {
        $http.get('/api/admin/plugins')
            .success(function(response, status, headers, config) {
                $scope.plugins = response.data;
            });
    };

    $scope.$on('$viewContentLoaded', function() {
        reload();
    });
});
