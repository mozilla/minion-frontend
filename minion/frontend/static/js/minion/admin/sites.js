// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

var minionAdminSitesModule = angular.module('minionAdminSitesModule', []);

minionAdminSitesModule.controller("AdminEditSiteController", function ($scope, dialog, site, plans) {
    
    $scope.site = site;
    $scope.plans = plans;
    /*
    First, understand how the backend issues the verificiation code.
    On every POST request to update the verification option, the backend
    re-issues a new verification value. This is not really a security check
    but we do this to simplify the logic (too many if-else makes
    the code messy).

    So, if the previous enable value is false, and if the user
    wants to re-enable the verification option, a typical ng-show will
    show the verification code. But if the user were to submit such
    request to re-enable verification, there will be a new code.

    We keep the user from seeing this cold value by doing a truth-table check.
    In the template we only do ng-show="prevous value && current_val" as 
    a way to short-circuit toggle. The truth table would be like
        |  e     |  d
    -----------------------
     E  | show   |  don't
    -----------------------
     D   | don't  |  don't

    e,d are user action and E and D are the previous value (from db).

    So unless both e and E are set to enable, we show. Otherwise, we hide.
   */
    if (site.verification == null)
        site.verification = {'enabled': false, 'value': null}
    $scope.prev_enabled_val = site.verification.enabled;
    $scope.plans = plans;
    $scope.cancel = function () {
        dialog.close(null);
    };

    $scope.submit = function(site) {
        if (site.verification.enabled != $scope.prev_enabled_val) {
            dialog.close(site);
        } else {
            dialog.close(null);
    }};
});

minionAdminSitesModule.controller("AdminCreateSiteController", function ($scope, dialog, plans, sites) {
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

minionAdminSitesModule.controller("AdminSitesController", function($scope, $routeParams, $http, $dialog) {

    $scope.navItems = app.navContext('admin');

    var reload = function() {
        $http.get('/api/admin/sites')
            .success(function(response, status, headers, config) {
                $scope.sites = response.data;
            });
    };

    $scope.editSite = function (site) {
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
                        var verify = site.verification;
                        $http.post('/api/admin/sites/' + site.id, 
                            {plans: site.plans, 
                             verification: {'enabled': verify.enabled, 'value': verify.value}}
                        ).success(function(response) {
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
                        var verify = {'enabled': site.verification.enabled, 'value': null};
                        $http.post('/api/admin/sites', {url: site.url, plans: site.plans, verification: verify}).success(function(response) {
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
