// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

var minionAdminPlansModule = angular.module('minionAdminPlansModule', []);

minionAdminPlansModule.controller("AdminCreatePlanController", function ($scope, dialog, plugins) {
    var workflow = [{
        plugin_name: "minion.plugins.basic.AlivePlugin",
        description: "",
        configuration: { } }];

    $scope.plan = { name: null, workflow: JSON.stringify(workflow, null, "  ") };

    $scope.cancel = function () {
        dialog.close(null);
    };

    var parseWorkflow = function (workflowString) {
        try {
            return jQuery.parseJSON(workflowString);
        } catch (e) {
            return null;
        }
    };

    var pluginExists = function (pluginName, plugins) {
        for (var i = 0; i < plugins.length; i++) {
            if (plugins[i].class === pluginName) {
                return true;
            }
        }
        return false;
    };

    $scope.submit = function() {
        var workflow = parseWorkflow($scope.plan.workflow);
        if (workflow == null) {
            $scope.error = "The workflow is invalid JSON";
            return;
        }
        // Check if the plugins exist
        for (var i = 0; i < workflow.length; i++) {
            if (!pluginExists(workflow[i].plugin_name, plugins)) {
                $scope.error = "Unknown plugin: " + workflow[i].plugin_name;
                return;
            }
        }
        var plan = { name: $scope.plan.name, description: $scope.plan.description, workflow: workflow };
        dialog.close(plan);
    };
});

minionAdminPlansModule.controller("AdminEditPlanController", function ($scope, dialog, plan, plugins) {
    $scope.plan = plan;
    $scope.plan.workflow = JSON.stringify($scope.plan.workflow, null, "  ");

    $scope.cancel = function () {
        dialog.close(null);
    };

    // TODO Refactor the following two - move them to the module? What to do in Angular.js?

    var parseWorkflow = function (workflowString) {
        try {
            return jQuery.parseJSON(workflowString);
        } catch (e) {
            return null;
        }
    };

    var pluginExists = function (pluginName, plugins) {
        for (var i = 0; i < plugins.length; i++) {
            if (plugins[i].class === pluginName) {
                return true;
            }
        }
        return false;
    };

    $scope.submit = function() {
        var workflow = parseWorkflow($scope.plan.workflow);
        if (workflow == null) {
            $scope.error = "The workflow is invalid JSON";
            return;
        }
        // Check if the plugins exist TODO Refactor into a utility class?
        for (var i = 0; i < workflow.length; i++) {
            if (!pluginExists(workflow[i].plugin_name, plugins)) {
                $scope.error = "Unknown plugin: " + workflow[i].plugin_name;
                return;
            }
        }
        var plan = { name: $scope.plan.name, description: $scope.plan.description, workflow: workflow };
        dialog.close(plan);
    };
});

minionAdminPlansModule.controller("AdminPlansController", function($scope, $routeParams, $http, $dialog) {

    $scope.navItems = app.navContext('admin');

    var reload = function() {
        $http.get('/api/admin/plans').success(function(response) {
            $scope.plans = response.data;
        });
    };

    $scope.editPlan = function (plan) {
        $http.get('/api/admin/plugins').success(function(response) {
            $scope.plugins = response.data;
            var d = $dialog.dialog({
                templateUrl: "static/partials/admin/plans/edit.html?x=" + new Date().getTime(),
                controller: "AdminEditPlanController",
                resolve: { plan: function() { return angular.copy(plan); },
                           plugins: function() { return $scope.plugins; } }
            });
            d.open().then(function(plan) {
                $http.post('/api/admin/plans/' + plan.name, plan).success(function(response) {
                    reload();
                });
            });
        });
    };

    $scope.createPlan = function () {
        $http.get('/api/admin/plugins').success(function(response) {
            $scope.plugins = response.data;
            var d = $dialog.dialog({
                templateUrl: "static/partials/admin/plans/create-plan.html?x=" + new Date().getTime(),
                controller: "AdminCreatePlanController",
                resolve: { plugins: function() { return $scope.plugins; } }

            });
            d.open().then(function(plan) {
                if (plan) {
                    $http.post('/api/admin/plans', plan).success(function(response) {
                        reload();
                    });
                }
            });
        });
    };

    $scope.removePlan = function(plan) {
        var title = 'Remove Plan';
        var msg = 'Are you sure you want to remove the ' + plan.name + ' plan?';
        var btns = [{result:false, label: 'Cancel'}, {result:true, label: 'OK', cssClass: 'btn-primary'}];
        $dialog.messageBox(title, msg, btns).open().then(function(result) {
            if (result) {
                $http.delete('/api/admin/plans/' + plan.name).success(function(response) {
                    reload();
                });
            }
        });
    };

    $scope.$on('$viewContentLoaded', function() {
        reload();
    });
});
