/**
 ** Usage: Add 'ui.bootstrap.modal.dialog' to app dependencies, and then '$dialog' to module dependencies.
 ** Use as:
 **   $dialog.messageBox('Title', 'Message', [{result:'cancel', label: 'Cancel'}, {result:'yes', label: 'Yes', cssClass: 'btn-primary'}])
 **     .open()
 **     .then(function(result) {
 **
 **     });
 **
 ** Or just:
 **
 **  $dialog.prompt('Title', 'Message').then(function(result) { } );
 **/

'use strict';

var  uiModalDialog = angular.module('ui.bootstrap.modal.dialog', []);
uiModalDialog.factory('$dialog', ['$rootScope', '$modal', function ($rootScope, $modal) {

    var prompt = function(title, message, buttons) {

    if(typeof buttons === 'undefined') {
    buttons = [
    {result:'cancel', label: 'Cancel'},
    {result:'yes', label: 'Yes', cssClass: 'btn-primary'}
    ];
    }

    var ModalCtrl = function($scope, $modalInstance) {
    $scope.title = title;
    $scope.message = message;
    $scope.buttons = buttons;

    $scope.close = function(result) {
    $modalInstance.close(result);
    };
    };

    return $modal.open({
templateUrl: 'template/dialog/message.html',
controller: ModalCtrl
}).result;
};

return {
prompt:     prompt,
              messageBox: function(title, message, buttons) {
                return {
open: function() {
        return prompt(title, message, buttons);
      }
                };
              }
};
}]);

uiModalDialog.run(["$templateCache", function (e) {
    e.put("template/dialog/message.html", '<div class="modal-header">   <h1>{{ title }}</h1></div><div class="modal-body">  <p>{{ message }}</p></div><div class="modal-footer">    <button ng-repeat="btn in buttons" ng-click="close(btn.result)" class=btn ng-class="btn.cssClass">{{ btn.label }}</button></div>')
    }]);
