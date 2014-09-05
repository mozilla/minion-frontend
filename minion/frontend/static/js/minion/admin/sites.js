// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.


var minionAdminSitesModule = angular.module('minionAdminSitesModule', []);


minionAdminSitesModule.controller("AdminEditSiteController", function ($scope, $modalInstance, site, plans) {
    $scope.site = site;
    $scope.plans = plans;

    $scope.cancel = function () {
        $modalInstance.close(null);
    };

    $scope.submit = function(site) {
        $modalInstance.close(site);
    };
});


minionAdminSitesModule.controller("AdminCreateSiteController", function ($scope, $modalInstance, plans, sites) {
    $scope.site = {url:"",plans:[],verification:{enabled:false,value:null}};
    $scope.plans = plans;

    $scope.cancel = function () {
        $modalInstance.close(null);
    };

    $scope.submit = function(site) {
        if (_.find(sites, function (s) { return s.url === site.url; })) {
            $scope.error = "The site already exists.";
        } else {
            $modalInstance.close(site);
        }
    };
});


minionAdminSitesModule.controller("AdminSitesCredentialController", function ($scope, $modalInstance, items) {
    $scope.schedule = {};
    $scope.auth = {};
    var keys = ['method',
                'url',
                'email',
                'username',
                'before_login_element_xpath',
                'login_button_xpath',
                'login_script',
                'after_login_element_xpath',
                'username',
                'username_field_xpath',
                'password_field_xpath',
                'expected_cookies'
                ];

    for(var i=0; i < keys.length; i++){
        $scope.auth[keys[i]] = (items.authData && !!items.authData[keys[i]]) ? items.authData[keys[i]] : "";
    }

    if(items.authData) {
        $scope.needUpdate = true;
    }

    // Default Authentication method menu to persona
    $scope.auth.method = $scope.auth.method  ? $scope.auth.method : 'persona';

    $scope.cancel = function () {
        $modalInstance.close(null);
    };

    $scope.submit = function() {
      $modalInstance.close($scope.auth);
    };

    $scope.remove = function() {
      $scope.auth.remove = true;
      $modalInstance.close($scope.auth);
    };
});




minionAdminSitesModule.controller("AdminSitesController", function($scope, $routeParams, $http, $modal, toaster) {
    $scope.navItems = app.navContext('admin');

    var reload = function() {
        $http.get('/api/admin/sites')
            .success(function(response, status, headers, config) {
                $scope.sites = response.data;
                $scope.credInfo = response.credInfo;
            });
    };

    $scope.editSite = function (site) {
        $http.get('/api/admin/plans').success(function(response) {
            $scope.plans = response.data;
                var d = $modal.open({
                    templateUrl: "static/partials/admin/sites/edit-site.html",
                    controller: "AdminEditSiteController",
                    resolve: { plans: function() { return $scope.plans; },
                               site: function() { return angular.copy(site); } }
                });
                d.result.then(function(site) {
                    if (site) {
                        var verify = site.verification;
                        $http.post('/api/admin/sites/' + site.id,
                                   {plans: site.plans,
                                    verification: {'enabled': verify.enabled,
                                                   'value': verify.value}}
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
                var d = $modal.open({
                    templateUrl: "static/partials/admin/sites/create-site.html",
                    controller: "AdminCreateSiteController",
                    resolve: { plans: function() { return $scope.plans; },
                               sites: function() { return $scope.sites; } }
                });
                d.result.then(function(site) {
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

    $scope.setCredentials = function(site, plan) {

        var items = {
            authData:$scope.credInfo[site] && $scope.credInfo[site][plan] && $scope.credInfo[site][plan].authData
        };

        var d = $modal.open({
            templateUrl: "static/partials/admin/site-credentials-dialog.html?date=" + new Date(),
            controller: "AdminSitesCredentialController",
            size:'lg',
            resolve: {
              items: function ()  {
                return items;
              }
            }
        });


        d.result.then(function(auth) {
            if(auth){
                var data = {
                    site:site,
                    plan:plan,
                    authData:auth
                };

                $http.put('api/setCredentials', data).
                  success(function(data, status) {
                      // Success Handler
                      if(data.success) {
                          reload();
                          toaster.pop('success', data.message, 'Site: ' + site + '</br>Plan: ' + plan, 5000);
                      }
                      else {
                          toaster.pop('error', data.message, 'Site: ' + site + '</br>Plan: ' + plan, 5000);
                      }
                  }).
                  error(function(data, status) {
                      // Error handler
                      toaster.pop('error', 'Error', 'Oh Snap! Something went wrong.', 5000);
                  });
            }
        });
    };
});
