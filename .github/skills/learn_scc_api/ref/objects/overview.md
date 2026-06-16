# Common Objects

## Base URL

The common object services APIs use the regional URLs as the base URLs. Be sure to use the correct URI for your region.

## About Objects

The Objects operations allow you to view all types of network objects and groups. You can list multiple objects with basic information, or specify an individual object to get more specific information. When creating objects be aware of object limitations within an organization and object naming requirements. Only networks and network groups are supported.

## About Networks

The Networks operations allow you to create, update, and delete network objects. An organization cannot have more than 100,000 network objects. You cannot change the subtype field of an existing object. To modify this field, delete the object and create a new one.

## About Network Groups

The Network Groups operations allow you to create, update, and delete network groups. An organization cannot have more than 10,000 network groups, and a single group cannot contain more than 1,500 objects

## API Specification

<https://pubhub.devnetcloud.com/media/cisco-security-cloud-control-api-documentation/docs/reference/security_cloud_control_common_objects_public_ap_is_1_0_0.yaml>
